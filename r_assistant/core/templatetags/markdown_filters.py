"""
Markdown template filters for rendering formatted text
"""

import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='markdown')
def markdown_filter(value):
    """
    Simple Markdown filter for Django templates
    Converts basic Markdown syntax to HTML
    """
    if not value:
        return ''
    
    # Convert the text
    html = str(value)
    
    # Code blocks first (```code```) - preserve content inside
    def replace_code_block(match):
        code_content = match.group(1)
        return f'<pre><code>{code_content}</code></pre>'
    
    html = re.sub(r'```(.*?)```', replace_code_block, html, flags=re.DOTALL)
    
    # Inline code (preserve backticks)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Headers
    html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Process lines for lists and paragraphs
    lines = html.split('\n')
    result_lines = []
    in_list = False
    list_type = None
    
    for line in lines:
        stripped = line.strip()
        
        # Check if this line is a list item
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list or list_type != 'ul':
                if in_list:
                    result_lines.append(f'</{list_type}>')
                result_lines.append('<ul>')
                in_list = True
                list_type = 'ul'
            result_lines.append(f'<li>{stripped[2:]}</li>')
            
        elif re.match(r'^\d+\. ', stripped):
            if not in_list or list_type != 'ol':
                if in_list:
                    result_lines.append(f'</{list_type}>')
                result_lines.append('<ol>')
                in_list = True
                list_type = 'ol'
            # Extract content after "number. "
            content = re.sub(r'^\d+\. ', '', stripped)
            result_lines.append(f'<li>{content}</li>')
            
        else:
            # Close any open list
            if in_list:
                result_lines.append(f'</{list_type}>')
                in_list = False
                list_type = None
            
            # Handle non-list lines
            if stripped:
                # Don't wrap lines that are already HTML tags
                if not (stripped.startswith('<') and stripped.endswith('>')):
                    result_lines.append(f'<p>{line}</p>')
                else:
                    result_lines.append(line)
            else:
                result_lines.append('')  # Empty line
    
    # Close any remaining list
    if in_list:
        result_lines.append(f'</{list_type}>')
    
    html = '\n'.join(result_lines)
    
    # Clean up extra empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'\n+', '\n', html)
    
    return mark_safe(html)


@register.filter(name='markdown_safe')
def markdown_safe_filter(value):
    """
    Safe Markdown filter that applies markdown-content CSS class
    """
    markdown_html = markdown_filter(value)
    return mark_safe(f'<div class="markdown-content">{markdown_html}</div>')