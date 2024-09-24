import pprint
from parser import OpensslCnf, Str, Comment, Section, KVP

# parse openssl.cnf file into AST
ast = OpensslCnf.load('/etc/ssl/openssl.cnf')

# modify AST: add comment and section to the end
ast.append(Str('\n'))
ast.append(Comment('  This is additional section'))
ast.append(Str('\n'))

engine_sect = Section('', 'engine_sect', '')
engine_sect.append(Str('\n'))
engine_sect.append(KVP('gost', '', '', 'gost_sect'))
engine_sect.append(Str('\n'))
ast.append(engine_sect)

# print modified AST
pprint.pprint(ast)

# save AST to file
ast.dump('/tmp/openssl-new.cnf')
