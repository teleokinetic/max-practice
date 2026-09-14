#!/usr/bin/env python3
"""Wrap max-src.html (artifact-style body: <title>, font link, <style>, markup, <script>) into a GitHub-Pages-ready index.html."""
import re,os
here=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(here,'max-src.html')).read()
m=re.search(r'<title>(.*?)</title>\s*',src,re.S); title=m.group(1) if m else "Max's Practice Map"
body=src.replace(m.group(0),'',1) if m else src
head=f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="robots" content="noindex, nofollow">
  <title>{title}</title>
  <meta name="theme-color" content="#FAF7F1">
  <link rel="manifest" href="manifest.webmanifest">
  <link rel="icon" href="icon-192.png" type="image/png">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <meta name="apple-mobile-web-app-title" content="Practice Map">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
</head>
<body>
'''
out=head+body.rstrip()+'''
<script>if ('serviceWorker' in navigator && location.protocol !== 'file:') { navigator.serviceWorker.register('sw.js').catch(function(){}); }</script>
</body>
</html>
'''
open(os.path.join(here,'index.html'),'w').write(out)
print('index.html',len(out))
