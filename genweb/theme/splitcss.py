import re

filename = 'stylesheets/genwebupc.css'
MAXSELECTORS = 1000

print "Spliting {} in {} selectors chunks".format(filename, MAXSELECTORS)

css = open(filename).read()

# Remove all comments except ones matching \* line XX ... *\
clean = re.sub(r'/\*(?!\sline).*?\*/', '', css, flags=re.DOTALL)


# temporary clean @* internal {} to []
def braces_replace(matchobj):
    m = matchobj.groups()
    mediabody = m[1].replace('}', ']').replace('{', '[')
    return m[0] + mediabody + m[2]

clean = re.sub(r'(\n@.*?\{)(.*?\}\s*)(\})', braces_replace, clean, flags=re.DOTALL)
items = re.findall(r'([^{}]*)(\{.*?\})', clean, re.DOTALL)

totalselector = 0
selectorcount = 0
lasttrimpoint = 0
filecount = 1

for selectors, body in items:
    newselectors = len(selectors.split(',')) - 1
    selectorcount += newselectors
    totalselector += newselectors
    if selectorcount > MAXSELECTORS:
        trimpoint = css.find(selectors)
        newcssname = 'stylesheets/genwebupc-{:0>2}.css'.format(filecount)
        print '> Writing {} with {} selectors'.format(newcssname,  selectorcount - newselectors)
        open(newcssname, 'w').write(css[lasttrimpoint:trimpoint])
        selectorcount = newselectors
        filecount += 1
        lasttrimpoint = int(trimpoint)

# Write the last chunk
newcssname = 'stylesheets/genwebupc-{:0>2}.css'.format(filecount)
open(newcssname, 'w').write(css[lasttrimpoint:])
print '> Writing {} with {} selectors'.format(newcssname,  selectorcount)
print totalselector
