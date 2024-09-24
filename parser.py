from abc import ABC
from enum import Enum

class TT(Enum):
    COM = 1
    SEC = 2
    STR = 3
    KVP = 4
    DIR = 5

class Token(ABC):
    def __init__(self, tt: TT):
        self.tt = tt

    def __repr__(self):
        return f'<{self.tt}> {str(self)}'

class Comment(Token):
    def __init__(self, comment):
        self.comment = comment
        super().__init__(TT.COM)

    def __str__(self):
        return '#' + self.comment

class Section(Token):
    def __init__(self, value_pre, value, value_post):
        self.value_pre = value_pre
        self.value = value
        self.value_post = value_post
        self.nodes:list[Token] = []
        super().__init__(TT.SEC)

    def append(self, t):
        self.nodes.append(t)

    def __str__(self):
        return f'[{self.value_pre}{self.value}{self.value_post}]' + ''.join(map(lambda n: str(n), self.nodes))

    def __repr__(self):
        return f'<{self.tt}> [{self.value_pre}{self.value}{self.value_post}]\n' + '\n'.join(map(lambda n: n.__repr__(), self.nodes)) + '\n'

class Str(Token):
    def __init__(self, value):
        self.value = value
        super().__init__(TT.STR)

    def __str__(self):
        return self.value

    def __repr__(self):
        return f'<{self.tt}> {str(self).replace("\r", r"\r").replace("\n", r"\n")}'

class KVP(Token):
    def __init__(self, key, key_post, value_pre, value):
        self.key = key
        self.key_post = key_post
        self.value_pre = value_pre
        self.value = value
        super().__init__(TT.KVP)

    def __str__(self):
        return f'{self.key}{self.key_post}={self.value_pre}{self.value}'

class Directive(Token):
    def __init__(self, directive, spacer, args):
        self.directive = directive
        self.spacer = spacer
        self.args = args
        super().__init__(TT.DIR)

    def __str__(self):
        return f'.{self.directive}{self.spacer}{self.args}'

class OpensslCnf:
    def __init__(self):
        self.nodes:list[Token] = []

    def append(self, t):
        self.nodes.append(t)

    def __str__(self):
        return ''.join(map(lambda n: str(n), self.nodes))

    def __repr__(self):
        return '\n'.join(map(lambda n: n.__repr__(), self.nodes))

    class parser():
        def __init__(self, fd):
            self.fd = fd
            self.read1()
        
        def read1(self):
            self.c = self.fd.read(1)
            return self.c

        def eat_comment(self):
            if self.c == '#':
                v = ''
                while True:
                    self.read1()
                    if not self.c or self.c == '\n' or self.c == '\r':
                        return Comment(v)
                    v += self.c

        def eat_str(self):
            if self.c.isspace():
                v = self.c
                while True:
                    self.read1()
                    if not self.c or not self.c.isspace():
                        return Str(v)
                    v += self.c

        def eat_sec(self):
            if self.c == '[':
                pre = v = post = ''

                while True:
                    self.read1()
                    if not self.c:
                        raise SystemError("invalid section")
                    if not self.c.isspace():
                        break
                    pre += self.c

                while True:
                    if not self.c:
                        raise SystemError("invalid section")
                    if self.c.isspace() or self.c == ']':
                        break

                    v += self.c
                    self.read1()

                while True:
                    if not self.c:
                        raise SystemError("invalid section")
                    if self.c == ']':
                        self.read1()
                        break
                    post += self.c
                    self.read1()

                return Section(pre, v, post)

        def eat_kv(self):
            if self.c.isalnum():
                key = key_post = value_pre = value = ''

                while True:
                    if self.c.isspace() or self.c == '=':
                        break
                    key += self.c
                    self.read1()
                    if not self.c or self.c == '\n' or self.c == '\r':
                        raise SystemError("invalid key")

                while True:
                    if self.c == '=':
                        break
                    key_post += self.c
                    self.read1()
                    if not self.c or self.c == '\n' or self.c == '\r':
                        raise SystemError("invalid key_after")

                while True:
                    self.read1()
                    if not self.c.isspace():
                        break
                    value_pre += self.c
                    if not self.c or self.c == '\n' or self.c == '\r':
                        raise SystemError("invalid value_pre")

                while True:
                    value += self.c
                    self.read1()
                    if not self.c or self.c == '#' or self.c == '\n' or self.c == '\r':
                        break

                return KVP(key, key_post, value_pre, value)

        def eat_directive(self):
            if self.c == '.':
                directive = spacer = args = ''
                while True:
                    self.read1()
                    if not self.c or self.c == '#' or self.c == '\n' or self.c == '\r':
                        return Directive(directive, spacer, args)
                    if self.c.isspace():
                        break

                    directive += self.c

                while True:
                    spacer += self.c
                    self.read1()
                    if not self.c or self.c == '#' or self.c == '\n' or self.c == '\r':
                        return Directive(directive, spacer, args)
                    if not self.c.isspace():
                        break

                while True:
                    args += self.c
                    self.read1()
                    if not self.c or self.c == '#' or self.c == '\n' or self.c == '\r':
                        return Directive(directive, spacer, args)

    def dump(self, filename):
        with open(filename, 'wt+', encoding='utf-8') as new:
            new.write(str(self))

    @staticmethod
    def load(filename):
        rv = OpensslCnf()

        with open(filename, 'rt', encoding='utf-8') as fd:
            ps = OpensslCnf.parser(fd)
            cur_section = rv
            while True:
                t = ps.eat_str() or \
                    ps.eat_comment() or \
                    ps.eat_sec() or \
                    ps.eat_kv() or \
                    ps.eat_directive() or \
                    None

                if not t:
                    break

                if t.tt == TT.SEC:
                    rv.append(t)
                    cur_section = t
                else:
                    cur_section.append(t)

                #print(f'<{t.tt}>' + str(t))
        return rv
