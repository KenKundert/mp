# Imports {{{1
from __future__ import division, print_function
import types as Types
import re as RE
import textwrap

# Strip Enclosing Braces {{{1
def _stripEnclosingBraces(text, stripBraces):
    if not stripBraces or len(text) <= 2:
        return text
    leadingIndex = 1 if text[0] == '{' else 0
    if text[-1] == '}':
        return text[leadingIndex:-1]
    else:
        return text[leadingIndex:]

# class Info {{{1
# Generic class
class Info(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __str__(self):
        return '%s<%s>' % (self.__class__.__name__, ', '.join(
            ['%s=%s' % item for item in self.__dict__.iteritems()]
        ))
    __repr__ = __str__

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError

# cull {{{1
# Cull Nones out of a list
def cull(l):
    """
    Return the list given as an argument with the Nones removed.

    Examples:
    >>> cull([])
    []
    >>> cull([None])
    []
    >>> cull(['a', None, 'b'])
    ['a', 'b']
    >>> cull(['a', 'b', 'c', None])
    ['a', 'b', 'c']
    >>> cull([None, 1, 2, 3])
    [1, 2, 3]
    """
    return [each for each in l if each != None]

# listToStr {{{1
# Like join, but with more flexibility
def listToStr(
    lst, sep = '', conj=None, pre = '', suf = '', head = '', foot = ''
):
    """
    Converts a list into a single string. All arguments are expected to be
    strings except the list, which can contain anything that can be converted
    into a string. Prefix (pre) and suffix (suf) are attached to the beginning
    and end of each item in the list. The last two item are then joined using
    the conjunction. Separator (sep) is used to join each item in the list; it
    is placed between each item in the list. Finally, the header (head) and
    footer (foot) are attached to the beginning and end of the resulting string.

    Examples:
    >>> listToStr([], ', ', ' and ')
    ''
    >>> listToStr(['a'], ', ', ' and ')
    'a'
    >>> listToStr(['a', 'b'], ', ', ' and ')
    'a and b'
    >>> listToStr(['a', 'b', 'c'], sep=', ', conj=' and ')
    'a, b and c'
    >>> listToStr([1, 2, 3], ', ', ' or ', '(', ')', 'Choose ', '.')
    'Choose (1), (2) or (3).'
    """
    body = []
    for item in lst:
        if item:
            body.append(pre + str(item) + suf)
    if body:
        if conj != None and len(body) > 1:
            body = body[0:-2] + [body[-2] + conj + body[-1]]
        return head + sep.join(body) + foot
    else:
        return ''

# conjoin {{{1
# Like join, but supports conjunction
def conjoin(lst, conj=' and ', sep=', '):
    """
    Conjunction Join
    Return the list joined into a string, where conj is used to join the last
    two items in the list, and sep is used to join the others.

    Examples:
    >>> conjoin([], ' or ')
    ''
    >>> conjoin(['a'], ' or ')
    'a'
    >>> conjoin(['a', 'b'], ' or ')
    'a or b'
    >>> conjoin(['a', 'b', 'c'])
    'a, b and c'
    """
    if type(lst) == set:
        lst = list(lst)
        lst.sort()
    if conj != None and len(lst) > 1:
        lst = lst[0:-2] + [lst[-2] + conj + lst[-1]]
    return sep.join(lst)

# listjoin {{{1
# Like join, but result is a list
def listjoin(items, sep):
    """
    List Join
    Return a list where the items of the provided list are interleaved with 
    copies of the separator.

    Examples:
    >>> listjoin([], ' or ')
    []

    >>> listjoin(['a', 'b', 'c'], ':')
    ['a', ':', 'b', ':', 'c']

    """
    out = (2*len(items)-1)*[sep]
    out[::2] = items
    return out

# examine {{{1
def examine( obj
    , name = None
    , shift = ''
    , indent = '    '
    , shiftFirst = True
    , all = True
    , equals = '='
    , addr = True
    , levels = 2
    , alreadySeen = None
):
    r"""
    Returns a string that contains a pretty-printed version of the argument and
    all of its contents.

    Examples:
    >>> print(examine([0, 1, 2, 'toothpaste'], 'numbers', addr=False))
    numbers = [
        [0] = 0 (int)
        [1] = 1 (int)
        [2] = 2 (int)
        [3] = "toothpaste" (string)
    ] (list)

    >>> print(examine({0: 'zero', 1: 'one'}, 'binary numbers', addr=False))
    binary numbers = {
        0 : "zero" (string)
        1 : "one" (string)
    } (dict)
    """
    # TODO: accept maxitems argument (avoids printing dictionaries, lists,
    #       tuples that are too long)
    #       accept maxlen argument for strings

    # examine() can be slow if it it produces a lot of output and we don't want
    # to accidentally use it in production code.
    assert __debug__

    firstShift = shift if shiftFirst else ''
    equals = ' %s ' % equals if equals else ' '
    nameEquals = '%s%s' % (name, equals) if name != None else ''
    contents = []
    if addr:
        address = ' 0x%x' % id(obj)
    else:
        address = ''
    # catch and terminate any self reference loops
    if alreadySeen == None:
        alreadySeen = set([])
    elif id(obj) in alreadySeen:
        return  '%s%s<<self referencing loop>> (%s)' % (firstShift, nameEquals, address)
    alreadySeen.add(id(obj))

    # Simple types
    if obj is None:
        contents += ['%s%s%s' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == type(False):
        contents += ['%s%s%s' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == type(0):
        contents += ['%s%s%s (int)' % (firstShift, nameEquals, str(obj))]
    #elif type(obj) == type(0L):
    #    contents += ['%s%s%s (long)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == type(0.0):
        contents += ['%s%s%s (real)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == type(0j):
        contents += ['%s%s%s (complex)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == type(""):
        contents += ['%s%s"%s" (string)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == type(u""):
        contents += ['%s%s"%s" (unicode)' % (firstShift, nameEquals, str(obj))]

    # Hierarchical types
    elif type(obj) == type(()):
        if len(obj) == 0 or levels <= 0:
            skipped = '' if levels > 0 else ' <<skipped>> '
            if name != None:
                contents += ["%s%s(%s) (tuple)" % (firstShift, nameEquals, skipped)]
            else:
                contents += ["%s(%s) (tuple)" % (firstShift, skipped)]
        else:
            if name != None:
                contents += ["%s%s(" % (firstShift, nameEquals)]
            for index, value in enumerate(obj):
                contents += [examine( value
                    , name='[%s]' % index
                    , shift=shift+indent
                    , indent=indent
                    , shiftFirst = True
                    , addr = addr
                    , levels = levels - 1
                    , alreadySeen = alreadySeen
                )]
            if name != None:
                contents += ['%s) (tuple%s)' % (shift, address)]
    elif type(obj) == type([]):
        # I used to test for generators here, but I could not figure out how to
        # do this easily in python3.
        #listtype = 'generated ' if type(obj) == Types.GeneratorType else ''
        listtype = ''
        if len(obj) == 0 or levels <= 0:
            skipped = '' if levels > 0 else ' <<skipped>> '
            if name != None:
                contents += ["%s%s[%s] (%slist)" % (firstShift, nameEquals, skipped, listtype)]
            else:
                contents += ["%s[%s] (%slist)" % (firstShift, skipped, listtype)]
        else:
            if name != None:
                contents += ["%s%s[" % (firstShift, nameEquals)]
            for index, value in enumerate(obj):
                contents += [examine( value
                    , name='[%s]' % index
                    , shift=shift+indent
                    , indent=indent
                    , shiftFirst = True
                    , addr = addr
                    , levels = levels - 1
                    , alreadySeen = alreadySeen
                )]
            if name != None:
                contents += ['%s] (%slist%s)' % (shift, listtype, address)]
    elif type(obj) == type({}):
        if len(obj.keys()) == 0 or levels <= 0:
            skipped = '' if levels > 0 else ' <<skipped>> '
            if name != None:
                contents += ["%s%s{%s} (dict%s)" % (firstShift, nameEquals, skipped, address)]
            else:
                contents += ["%s{%s} (dict%s)" % (firstShift, skipped, address)]
        else:
            if name != None:
                contents += ["%s%s{" % (firstShift, nameEquals)]
            for key in sorted(obj.keys()):
                contents += [examine( obj[key]
                    , name=str(key)
                    , shift=shift+indent
                    , indent=indent
                    , shiftFirst = True
                    , equals = ':'
                    , addr = addr
                    , levels = levels - 1
                    , alreadySeen = alreadySeen
                )]
            if name != None:
                contents += ['%s} (dict%s)' % (shift, address)]
    elif type(obj) == set:
        if len(obj) == 0 or levels <= 0:
            skipped = '' if levels > 0 else ' <<skipped>> '
            if name != None:
                contents += ["%s%s(%s) (set%s)" % (firstShift, nameEquals, skipped, address)]
            else:
                contents += ["%s(%s) (set%s)" % (firstShift, skipped, address)]
        else:
            if name != None:
                contents += ["%s%s(" % (firstShift, nameEquals)]
            for index, each in enumerate(sorted(obj)):
                contents += [examine(each
                    , name=index
                    , shift=shift+indent
                    , indent=indent
                    , shiftFirst = True
                    , equals = ':'
                    , addr = addr
                    , levels = levels - 1
                    , alreadySeen = alreadySeen
                )]
        if name != None:
            contents += ['%s) (set%s)' % (shift, address)]
    elif hasattr(obj, '__dict__'):
    #type(obj) == Types.InstanceType or isinstance(obj, object):
        # rather than testing the type at this point, perhaps I should just
        # check for __dict__ (and perhaps __class__
        if hasattr(obj, '__class__'):
            insttype = 'instance of %s%s' % (obj.__class__, address)
        else:
            insttype = '%s%s' % (type(obj), address)
        if levels <= 0:
            skipped = '' if levels > 0 else ' <<skipped>> '
            if name != None:
                contents += ["%s%s<%s> (%s)" % (firstShift, nameEquals, skipped, insttype)]
            else:
                contents += ["%s<%s> (%s)" % (firstShift, skipped, insttype)]
        else:
            if name != None:
                contents += ["%s%s<" % (firstShift, nameEquals)]
            uninteresting = RE.compile(r'__[a-zA-Z0-9_]*__')
            for key in sorted(obj.__dict__.keys()):
                # does not print values of underlying class variables
                value = obj.__dict__[key]
                if all or not uninteresting.match(key):
                    contents += [examine( value
                        , name=key
                        , shift=shift+indent
                        , indent=indent
                        , shiftFirst = True
                        , addr = addr
                        , levels = levels - 1
                        , alreadySeen = alreadySeen
                    )]
        if name != None:
            contents += ['%s> (%s)' % (shift, insttype)]
    else:
        # this case handles None plus all the unprintable types
        if obj is None or all:
            contents += ['%s%s%s' % (firstShift, nameEquals, str(obj))]
    # this still does not handle new-style classes, which are essentially user
    # defined types

    alreadySeen.remove(id(obj))
    return '\n'.join(contents)

# toStr {{{1
# a simple replacement for examine()
import types
def toStr(obj, name=None, verbose=False, _level=0, _seen=None):
    r"""
    Returns a string that contains a pretty-printed version of the argument and
    all of its contents. Tries to avoid infinite recursions.

    Examples:
    >>> print('procedure =', toStr([0, 1, 2, 'toothpaste']))
    procedure = [
        0
        1
        2
        'toothpaste'
    ]

    >>> print('boolean =', toStr({0: 'zero', 1: 'one'}))
    boolean = {
        0: 'zero'
        1: 'one'
    }

    >>> print('set =', toStr(set(['heads', 'tails'])))
    set = set([
        'heads'
        'tails'
    ])

    >>> class Foo:
    ...     pass
    >>> x=Foo()
    >>> x.bar = 'bar'
    >>> x.baz = 'baz'
    >>> print(toStr(x, 'my data', True)) # doctest: +ELLIPSIS
    my data = instance of kskutils.Foo (id=...):
        bar = 'bar'
        baz = 'baz'
    """
    def indent(relativeLevel=0):
        return (_level+relativeLevel)*'    '
    def showID(obj):
        if verbose:
            return ' (id=%s)' % id(obj)
        else:
            return ''
    if _seen == None:
        _seen = set()
    if name:
        prefix = '%s = ' % name
    else:
        prefix = ''
    args = (verbose, _level+1, _seen)
    output = []
    if type(obj) == dict:
        _seen.add(id(obj))
        output += ['%s{' % prefix]
        for key in sorted(obj.keys()):
            value = obj[key]
            if id(value) in _seen:
                output += ['%s%r: <<recursion%s>>' % (indent(1), key, showID(value))]
            else:
                output += ['%s%r: %s' % (
                    indent(1), key, toStr(value, None, *args)
                )]
        output += ['%s}%s' % (indent(0), showID(obj))]
    elif type(obj) == list:
        _seen.add(id(obj))
        output += ['%s[' % prefix]
        for each in obj:
            if id(each) in _seen:
                output += ['%s<<recursion%s>>' % (indent(1), showID(each))]
            else:
                output += ['%s%s' % (
                    indent(1), toStr(each, None, *args)
                )]
        output += ['%s]%s' % (indent(0), showID(obj))]
    elif type(obj) == tuple:
        _seen.add(id(obj))
        output += ['%s(' % prefix]
        for each in obj:
            if id(each) in _seen:
                output += ['%s<<recursion%s>>' % (indent(1), showID(each))]
            else:
                output += ['%s%s' % (
                    indent(1), toStr(each, None, *args)
                )]
        output += ['%s)%s' % (indent(0), showID(obj))]
    elif type(obj) == set:
        _seen.add(id(obj))
        output += ['%sset([' % prefix]
        for each in sorted(obj):
            if id(each) in _seen:
                output += ['%s<<recursion%s>>' % (indent(1), showID(each))]
            else:
                output += ['%s%s' % (
                    indent(1), toStr(each, None, *args)
                )]
        output += ['%s])%s' % (indent(0), showID(obj))]
    elif hasattr(obj, '__dict__'):
        _seen.add(id(obj))
        if type(obj) == Types.InstanceType:
            output += ['%sinstance of %s%s:' % (prefix, obj.__class__, showID(obj))]
        else:
            output += ['%s%s' % (prefix, str(obj.__class__))]
        for each in sorted(obj.__dict__.keys()):
            value = obj.__dict__[each]
            if id(value) in _seen:
                output += ['%s%s = <<recursion%s>>' % (indent(1), each, showID(value))]
            else:
                output += ['%s%s = %s' % (
                    indent(1), each, toStr(value, None, *args)
                )]
    else:
        output += [prefix + obj.__repr__()]
    return '\n'.join(output)


# title {{{1
def title(text, level=2, overline=False, newline=True):
    r"""
    Returns the string given as an argument with an underline and perhaps an
    overline.

    Examples:
    >>> print(title('Hello World!'))
    <BLANKLINE>
    Hello World!
    ============

    >>> print(title('Hello World!', 3, newline=False))
    Hello World!
    ------------

    >>> print(title('Hello World!', '~', newline=False))
    Hello World!
    ~~~~~~~~~~~~

    >>> print(title('Hello World!', 0, True, False))
    ############
    Hello World!
    ############

    """
    try:
        char = '#*=-^"'[level]
    except TypeError:
        char = str(level)
    if newline:
        result = ['']
    else:
        result = []
    if overline:
        result.append(len(text)*char)
    result.append(text)
    result.append(len(text)*char)
    return '\n'.join(result)

# wrap {{{1
def wrap(paragraphs, stripBraces=True):
    r"""{
    Accept a list of paragraphs and return a string with each paragraph dedented
    and wrapped.

    It is a personal convention to use '''{ to start a long comment and }''' to
    end it because my vim color rules are trained to recognize this as a
    and this comment is more reliable than simply using ''' (because vim cannot
    tell by looking at a small section of text whether the comment is starting
    or ending. Thus, by default, this command removes leading and trailing
    braces.

    Examples:
    >>> print(wrap(['    Hello', '    World!']))
    Hello
    <BLANKLINE>
    World!

    >>> print(wrap(['{    Hello}', '{    World!}']))
    Hello
    <BLANKLINE>
    World!

    >>> print(wrap(['{    Hello}', '{    World!}'], False))
    {    Hello}
    <BLANKLINE>
    {    World!}

    }"""
    return '\n\n'.join([
        textwrap.fill(
            textwrap.dedent(
                _stripEnclosingBraces(
                    each, stripBraces
                )
            )
        ) for each in paragraphs
    ])

# dedent {{{1
def dedent(text, stripBraces=True):
    r"""{
    Remove common indentation.

    It is a personal convention to use '''{ to start a long comment and }''' to
    end it because my vim color rules are trained to recognize this as a
    and this comment is more reliable than simply using ''' (because vim cannot
    tell by looking at a small section of text whether the comment is starting
    or ending. Thus, by default, this command removes leading and trailing
    braces.

    Examples:
    >>> print(dedent('''\
    ...     Hello
    ...     World!
    ... '''))
    Hello
    World!
    <BLANKLINE>

    >>> print(dedent('''{\
    ...     Hello
    ...     World!
    ... }'''))
    Hello
    World!
    <BLANKLINE>

    >>> print(dedent('''{\
    ...     Hello
    ...     World!
    ... }''', False))
    {    Hello
        World!
    }

    }"""
    return textwrap.dedent(
        _stripEnclosingBraces(
            text, stripBraces
        )
    )

# indent {{{1
def indent(text, spaces = 0):
    r"""{
    Add indentation.

    Examples:
    >>> print(indent('Hello\nWorld!', 4))
        Hello
        World!

    }"""
    return '\n'.join([
        spaces*' '+line if line else line for line in text.split('\n')
    ])

# redent {{{1
def redent(text, spaces = 0, stripBraces=True):
    r"""{
    Remove common indentation and then apply a new indentation.

    It is a personal convention to use '''{ to start a long comment and }''' to
    end it because my vim color rules are trained to recognize this as a
    and this comment is more reliable than simply using ''' (because vim cannot
    tell by looking at a small section of text whether the comment is starting
    or ending. Thus, by default, this command removes leading and trailing
    braces.

    Examples:
    >>> print(redent('''\
    ...     Hello
    ...     World!
    ... ''', 8))
            Hello
            World!
    <BLANKLINE>

    >>> print(redent('''{\
    ...     Hello
    ...     World!
    ... }''', 8))
            Hello
            World!
    <BLANKLINE>

    >>> print(redent('''{\
    ...     Hello
    ...     World!
    ... }''', 8, False))
            {    Hello
                World!
            }

    }"""
    return indent(dedent(text, stripBraces), spaces=spaces)

# Tests are run from ./test
#if __name__ == "__main__":
#    import doctest
#    doctest.testmod()

# vi:ai:sw=4:sts=4:et:ff=unix
