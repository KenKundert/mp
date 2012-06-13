# Imports {{{1
import types as Types
import re as RE

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
    >>> print examine([0, 1, 2, 'toothpaste'], 'numbers', addr=False)
    numbers = [
        [0] = 0 (int)
        [1] = 1 (int)
        [2] = 2 (int)
        [3] = "toothpaste" (string)
    ] (list)

    >>> print examine({0: 'zero', 1: 'one'}, 'binary numbers', addr=False)
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
    if type(obj) == Types.NoneType:
        contents += ['%s%s%s' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == Types.BooleanType:
        contents += ['%s%s%s' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == Types.IntType:
        contents += ['%s%s%s (int)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == Types.LongType:
        contents += ['%s%s%s (long)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == Types.FloatType:
        contents += ['%s%s%s (real)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == Types.ComplexType:
        contents += ['%s%s%s (complex)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == Types.StringType:
        contents += ['%s%s"%s" (string)' % (firstShift, nameEquals, str(obj))]
    elif type(obj) == Types.UnicodeType:
        contents += ['%s%s"%s" (unicode)' % (firstShift, nameEquals, str(obj))]

    # Hierarchical types
    elif type(obj) == Types.TupleType:
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
    elif type(obj) in [Types.ListType, Types.GeneratorType]:
        listtype = 'generated ' if type(obj) == Types.GeneratorType else ''
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
    elif type(obj) == Types.DictType:
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
        if type(obj) == Types.NoneType or all:
            contents += ['%s%s%s' % (firstShift, nameEquals, str(obj))]
    # this still does not handle new-style classes, which are essentially user
    # defined types

    alreadySeen.remove(id(obj))
    return '\n'.join(contents)

# toStr {{{1
# a simple replacement for examine()
import types
def toStr(obj, level = 0):
    r"""
    Returns a string that contains a pretty-printed version of the argument and
    all of its contents.

    Examples:
    >>> print 'procedure =', toStr([0, 1, 2, 'toothpaste'])
    procedure = [
        0,
        1,
        2,
        'toothpaste',
    ]

    >>> print 'boolean =', toStr({0: 'zero', 1: 'one'})
    boolean = {
        0: 'zero',
        1: 'one',
    }

    >>> print 'set =', toStr(set(['heads', 'tails']))
    set = set([
        'heads',
        'tails',
    ])

    >>> class Foo:
    ...     pass
    >>> x=Foo()
    >>> x.bar = 'bar'
    >>> x.baz = 'baz'
    >>> print 'foo =', toStr(x)
    foo = instance of kskutils.Foo:
        bar = 'bar'
        baz = 'baz'
    """
    def indent(relativeLevel=0):
        return (level+relativeLevel)*'    '
    output = []
    if type(obj) == dict:
        # for an example of a version that prints dictionaries in a prespecified
        # order, see contacts/ab.py
        output += ['{']
        for key, value in sorted(obj.items()):
            output += ['%s%s: %s,' % (
                indent(1), key.__repr__(), toStr(value, level+1)
            )]
        output += ['%s}' % indent(0)]
    elif type(obj) == list:
        output += ['[']
        for each in obj:
            output += ['%s%s,' % (
                indent(1), toStr(each, level+1)
            )]
        output += ['%s]' % indent(0)]
    elif type(obj) == tuple:
        output += ['(']
        for each in obj:
            output += ['%s%s,' % (
                indent(1), toStr(each, level+1)
            )]
        output += ['%s)' % indent(0)]
    elif type(obj) == set:
        output += ['set([']
        for each in sorted(obj):
            output += ['%s%s,' % (
                indent(1), toStr(each, level+1)
            )]
        output += ['%s])' % indent(0)]
    elif hasattr(obj, '__dict__'):
        if type(obj) == types.InstanceType:
            output += ['instance of %s:' % obj.__class__]
        else:
            output += [str(obj.__class__)]
        for each in sorted(obj.__dict__.keys()):
            output += ['%s%s = %s' % (
                indent(1), each, toStr(obj.__dict__[each], level+1)
            )]
    else:
        output += [obj.__repr__()]
    return '\n'.join(output)


# title {{{1
def title(text, level=2, overline=False, newline=True):
    r"""
    Returns the string given as an argument with an underline and perhaps an
    overline.

    Examples:
    >>> print title('Hello World!')
    <BLANKLINE>
    Hello World!
    ============

    >>> print title('Hello World!', 3, newline=False)
    Hello World!
    ------------

    >>> print title('Hello World!', '~', newline=False)
    Hello World!
    ~~~~~~~~~~~~

    >>> print title('Hello World!', 0, True, False)
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
def wrap(paragraphs):
    r"""
    Accept a list of paragraphs and return a string with each paragraph dedented
    and wrapped.

    Examples:
    >>> print wrap(['    Hello', '    World!'])
    Hello
    <BLANKLINE>
    World!

    """
    from textwrap import dedent, fill
    return '\n\n'.join([
        fill(dedent(each)) for each in paragraphs
    ])

# Tests are run from ./test
#if __name__ == "__main__":
#    import doctest
#    doctest.testmod()

# vi:ai:sw=4:sts=4:et:ff=unix
