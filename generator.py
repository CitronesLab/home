import json
import os
import math
import re
from string import Template
from datetime import datetime
from urllib.parse import quote

PER_PAGE = 7
MONTHS_ES = ['enero','febrero','marzo','abril','mayo','junio',
             'julio','agosto','septiembre','octubre','noviembre','diciembre']

def format_date(date_str):
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return f"{dt.day} de {MONTHS_ES[dt.month - 1]} de {dt.year}"
    except Exception:
        return date_str

def strip_html(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html or '')).strip()

def make_preview(text, length=160):
    t = strip_html(text)
    if len(t) > length:
        t = t[:length].rsplit(' ', 1)[0] + '…'
    return t

def render_media(media, project_id, fallback_alt=''):
    if not media:
        return ''
    out = ['<div class="media">']
    for m in media:
        t = m.get('type')
        if t == 'image':
            url = resolve_src(m.get('src', ''), project_id, base='posts')
            alt = m.get('alt') or m.get('caption') or fallback_alt
            cap = f'<figcaption>{m["caption"]}</figcaption>' if m.get('caption') else ''
            out.append(
                f'<figure><img src="{url}" alt="{alt}" '
                f'loading="lazy" decoding="async">{cap}</figure>'
            )
        elif t == 'youtube':
            out.append(
                '<div class="video"><iframe '
                f'src="https://www.youtube-nocookie.com/embed/{m["id"]}" '
                'title="YouTube video" allow="accelerometer; autoplay; '
                'clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                'allowfullscreen loading="lazy"></iframe></div>'
            )
    out.append('</div>')
    return '\n'.join(out)

def render_entry(entry, project_id):
    return f"""
    <article class="entry">
      <div class="entry-date">{format_date(entry.get('date', ''))}</div>
      <h2>{entry.get('title', '')}</h2>
      <div class="content">{entry.get('content', '')}</div>
      {render_media(entry.get('media', []), project_id, fallback_alt=entry.get('title', ''))}
    </article>
    """

def page_file(pid, n):
    return f'{pid}.html' if n == 1 else f'{pid}-p{n}.html'

def generate_site():
    with open('content/posts.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    site_title = data.get('site_title', 'CitronesLab')
    site_desc  = data.get('site_description', '')
    projects   = data.get('projects', [])

    with open('templates/index.html', 'r', encoding='utf-8') as f:
        index_tpl = Template(f.read())
    with open('templates/project.html', 'r', encoding='utf-8') as f:
        project_tpl = Template(f.read())

    # Limpiar posts/ para no dejar HTML huérfanos de proyectos eliminados
    os.makedirs('posts', exist_ok=True)
    for fname in os.listdir('posts'):
        if fname.endswith('.html'):
            os.remove(os.path.join('posts', fname))

    cards = []

    for p in projects:
        pid     = p['id']
        ptitle  = p['title']
        pdesc   = p.get('description', '')
        cover   = p.get('cover', '')
        entries = sorted(p.get('entries', []),
                         key=lambda e: e.get('date', ''), reverse=True)

        img_dir = os.path.join('images', pid)
        os.makedirs(img_dir, exist_ok=True)
        gitkeep = os.path.join(img_dir, '.gitkeep')
        if not os.path.exists(gitkeep):
            open(gitkeep, 'w').close()
    
        

        # ----- Tarjeta del home -----
        count = len(entries)
        if entries:
            latest = entries[0]
            preview = make_preview(latest.get('preview') or latest.get('content', ''))
            date_line = (f'Última: {format_date(latest.get("date", ""))} '
                         f'&mdash; {latest.get("title", "")}')
        else:
            preview = 'Este proyecto todavía no tiene entradas.'
            date_line = 'Sin entradas aún'

        cover_html = (f'<img class="cover" src="{resolve_src(cover, pid, base="root")}" '
              f'alt="{ptitle}" loading="lazy">' if cover else '')

        cards.append(f"""
        <div class="card">
          {cover_html}
          <div class="body">
            <div class="count">{count} entrada{'s' if count != 1 else ''}</div>
            <h2><a href="posts/{page_file(pid, 1)}">{ptitle}</a></h2>
            <div class="date">{date_line}</div>
            <p class="preview">{preview}</p>
            <a class="more" href="posts/{page_file(pid, 1)}">Ver proyecto &rarr;</a>
          </div>
        </div>
        """)

        # ----- Páginas del proyecto (paginadas cada 7 entradas) -----
        total = len(entries)
        pages = max(1, math.ceil(total / PER_PAGE))

        for i in range(pages):
            page_num = i + 1
            chunk = entries[i * PER_PAGE:(i + 1) * PER_PAGE]

            entries_html = ''.join(render_entry(e, pid) for e in chunk)
            if total == 0:
                entries_html = ('<p style="color:#9a9aa5">'
                                'Aún no hay entradas en este proyecto.</p>')

            # Paginación (solo si hay más de una página)
            if pages > 1:
                parts = ['<div class="pagination">']
                if page_num > 1:
                    parts.append(f'<a href="{page_file(pid, page_num - 1)}">'
                                 '&larr; Más recientes</a>')
                else:
                    parts.append('<span class="disabled">&larr; Más recientes</span>')

                parts.append(f'<span class="current">Página {page_num} de {pages}</span>')

                if page_num < pages:
                    parts.append(f'<a href="{page_file(pid, page_num + 1)}">'
                                 'Más antiguas &rarr;</a>')
                else:
                    parts.append('<span class="disabled">Más antiguas &rarr;</span>')
                parts.append('</div>')
                pagination_html = ''.join(parts)
            else:
                pagination_html = ''

            html = project_tpl.substitute(
                site_title=site_title,
                project_title=ptitle,
                project_description=pdesc,
                entries_html=entries_html,
                pagination_html=pagination_html,
            )
            with open(f'posts/{page_file(pid, page_num)}', 'w', encoding='utf-8') as f:
                f.write(html)

    # ----- Home -----
    index_html = index_tpl.substitute(
        site_title=site_title,
        site_description=site_desc,
        projects_html='\n'.join(cards),
    )
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

    print('✅ Sitio CitronesLab generado correctamente.')

def resolve_src(src, project_id, base='posts'):
    """
    Resuelve el src de una imagen.
    - Si es una URL absoluta (http/https/data), la deja tal cual.
    - Si es un nombre relativo, lo mapea a images/<project_id>/<nombre>.
    - base='posts' → prefijo '../images' (desde posts/*.html)
    - base='root'  → prefijo 'images'   (desde index.html)
    """
    if not src:
        return ''
    src = src.strip()
    if src.startswith(('http://', 'https://', 'data:', '//')):
        return src

    # Tolerar que el usuario escriba "images/huerto-inteligente/foto.jpg"
    for pref in (f'images/{project_id}/', f'/images/{project_id}/'):
        if src.startswith(pref):
            src = src[len(pref):]

    prefix = '../images' if base == 'posts' else 'images'
    # quote() preserva '/' pero codifica espacios y acentos → rutas web válidas
    return quote(f'{prefix}/{project_id}/{src}')

def render_media(media, project_id, fallback_alt=''):
    if not media:
        return ''
    out = ['<div class="media">']
    for m in media:
        t = m.get('type')
        if t == 'image':
            url = resolve_src(m.get('src', ''), project_id, base='posts')
            alt = m.get('alt') or m.get('caption') or fallback_alt
            cap = f'<figcaption>{m["caption"]}</figcaption>' if m.get('caption') else ''
            out.append(
                f'<figure><img src="{url}" alt="{alt}" '
                f'loading="lazy" decoding="async">{cap}</figure>'
            )
        elif t == 'youtube':
            out.append(
                '<div class="video"><iframe '
                f'src="https://www.youtube-nocookie.com/embed/{m["id"]}" '
                'title="YouTube video" allow="accelerometer; autoplay; '
                'clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                'allowfullscreen loading="lazy"></iframe></div>'
            )
    out.append('</div>')
    return '\n'.join(out)
    
if __name__ == '__main__':
    generate_site()
