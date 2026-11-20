import json
import os
from string import Template

def generate_site():
    # 1. Leer el JSON
    with open('content/posts.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    site_title = data.get('site_title', 'Mi Bitácora')
    topics = data.get('topics', [])
    
    # 2. Leer plantillas
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        index_tpl = Template(f.read())
    with open('templates/post.html', 'r', encoding='utf-8') as f:
        post_tpl = Template(f.read())
    
    # 3. Crear carpeta de posts si no existe
    os.makedirs('posts', exist_ok=True)
    
    topics_html = ""
    
    # 4. Generar cada tema
    for topic in topics:
        topic_id = topic['id']
        
        # Generar la página individual
        post_html = post_tpl.substitute(
            title=topic['title'],
            site_title=site_title,
            content=topic['content']
        )
        with open(f'posts/{topic_id}.html', 'w', encoding='utf-8') as f:
            f.write(post_html)
        
        # Crear la tarjeta para el Home
        card = f"""
        <div class="card">
            <h2><a href="posts/{topic_id}.html">{topic['title']}</a></h2>
            <p>{topic['preview']}</p>
            <a href="posts/{topic_id}.html">Leer más →</a>
        </div>
        """
        topics_html += card
        
    # 5. Generar el Home
    index_html = index_tpl.substitute(
        site_title=site_title,
        topics_html=topics_html
    )
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
        
    print("✅ Sitio generado correctamente.")

if __name__ == '__main__':
    generate_site()