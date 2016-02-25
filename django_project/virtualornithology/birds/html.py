from .models import Url
import regex

URL_RE = regex.compile(r'(https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|])')
HASHTAG_RE = regex.compile(r'(#[\w]+)', regex.UNICODE)
MENTION_RE = regex.compile(r'(@[\w]+)', regex.UNICODE)


def beautify_html(text, sources=None):
    global URL_RE
    idx = 0
    match = URL_RE.search(text[idx:])

    if match:
        short_url = match.group()
        span = match.span()

        if sources is None:
            try:
                expanded_url = Url.objects.get(short=short_url).url
            except Url.DoesNotExist:
                print(short_url, 'does not exist')
                expanded_url = short_url

            domain = expanded_url.split('//')[1].split('/')[0]

            formatted_url = '<a target="_blank" href="{0}">{1}</a>'.format(expanded_url, domain)

            if formatted_url[0:3] == 'www':
                formatted_url = formatted_url[3:]
            text = text[0:span[0]] + formatted_url + text[span[1]:]
        else:
            url = [u for u in sources if u['url'] == short_url]
            if url:
                formatted_url = '<a target="_blank" href="{0}">{1}</a>'.format(url[0]['expanded_url'], url[0]['display_url'])
                text = text[0:span[0]] + formatted_url + text[span[1]:]

    tags = HASHTAG_RE.findall(text)
    for t in tags:
        text = text.replace(t, '<a href="https://twitter.com/hashtag/{0}" target="_blank">{1}</a>'.format(t[1:], t))

    mentions = MENTION_RE.findall(text)
    for m in mentions:
        text = text.replace(m, '<a href="https://twitter.com/intent/user?screen_name={0}" target="_blank">{1}</a>'.format(m[1:], m))

    return text
