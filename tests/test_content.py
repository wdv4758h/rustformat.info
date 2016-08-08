# -*- encoding: utf-8 -*-
import sys
from subprocess import run, PIPE
from tempfile import NamedTemporaryFile, gettempdir
from os import remove

import pytest


def run_rust(code):
    with NamedTemporaryFile(suffix='.rs') as file:
        file.write(b'fn main () {\n')
        file.write('    let s = {};\n'.format(code).encode())
        file.write(b'    println!("{}", s);\n')
        file.write(b'}')
        file.flush()
        run(["rustc", "--out-dir={}".format(gettempdir()), file.name])
        executable = file.name.rsplit('.')[0]
        result = run([executable], stdout=PIPE).stdout
        remove(executable)
    return result.decode().rstrip('\n')


def test_simple():
    """
    # Basic formatting

    Simple positional formatting is probably the most common use-case. Use it
    if the order of your arguments is not likely to change and you only have
    very few elements you want to concatenate.

    Since the elements are not represented by something as descriptive as a
    name this simple style should only be used to format a relatively small
    number of elements.
    """
    old_result = '%s %s' % ('one', 'two', )
    new_result = '{} {}'.format('one', 'two')
    rust_result = 'format!("{} {}", "one", "two")'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == 'one two'  # output


def test_simple_2():
    old_result = '%d %d' % (1, 2)
    new_result = '{} {}'.format(1, 2)
    rust_result = 'format!("{} {}", 1, 2)'

    assert old_result == new_result == run_rust(rust_result)
    assert new_result == "1 2"  # output


def test_simple_3():
    """
    With Python's new style formatting it is possible (and in Python 2.6 even mandatory)
    to give placeholders an explicit positional index.

    This allows for re-arranging the order of display without changing the
    arguments.
    """
    new_result = '{1} {0}'.format('one', 'two')
    rust_result = 'format!("{1} {0}", "one", "two")'

    assert new_result == run_rust(rust_result)
    assert new_result == 'two one'  # output


def test_conversion_flags():
    """
    # Value conversion

    The Python's new-style simple formatter calls by default the [`__format__()`][1]
    method of an object for its representation. If you just want to render the
    output of `str(...)` or `repr(...)` you can use the `!s` or `!r` conversion
    flags.

    In %-style you usually use `%s` for the string representation but there is
    `%r` for a `repr(...)` conversion.

    [1]: https://docs.python.org/3/reference/datamodel.html#object.__format__

    """
    class Data(object):
        def __str__(self):
            return 'str'

        def __repr__(self):
            return 'repr'

    old_result = '%s %r' % (Data(), Data())
    new_result = '{0!s} {0!r}'.format(Data())

    assert new_result == 'str repr'  # output
    assert new_result == old_result


@pytest.mark.xfail(sys.version_info < (3,), reason="!a not available in Python 2")
def test_ascii_conversion():
    """
    In Python 3 there exists an additional conversion flag that uses the output
    of `repr(...)` but uses `ascii(...)` instead.
    """
    class Data(object):
        def __repr__(self):
            return 'räpr'

    new_result = '{0!r} {0!a}'.format(Data())

    assert new_result == 'räpr r\\xe4pr'  # output


def test_debug_conversion():
    """
    In Rust there exists an additional conversion flag that can use for who implmeneted [std::fmt::Debug][1] trait:

    [1]: https://doc.rust-lang.org/std/fmt/trait.Debug.html
    """

    rust_result = 'format!("{:?}", vec![1, 2, 3])'

    assert run_rust(rust_result) == '[1, 2, 3]'


def test_string_pad_align():
    """
    # Padding and aligning strings

    By default values are formatted to take up only as many characters as
    needed to represent the content. It is however also possible to define that
    a value should be padded to a specific length.

    Unfortunately the default alignment differs between Python's old and new style
    formatting. The old style defaults to right aligned while for new style
    it's left.

    Align right:
    """
    old_result = '%10s' % ('test', )
    new_result = '{:>10}'.format('test')
    rust_result = 'format!("{:>10}", "test")'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == '      test'  # output


def test_string_pad_align_2():
    """
    Align left:
    """

    old_result = '%-10s' % ('test', )
    new_result = '{:10}'.format('test')
    rust_result = 'format!("{:10}", "test")'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == 'test      '  # output


def test_string_variable_pad_align():
    """
    By argument:

    In the previous example, the value '10' is encoded as part of the format
    string.  However, it is possible to also supply such values as an
    argument.
    """
    old_result = '%*s' % (-8, 'test')
    new_result = '{:<{}s}'.format('test', 8)
    rust_result = 'format!("{:<1$}", "test", 8)'    # TODO, more options

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == 'test    '  # output


def test_string_pad_align_3():
    """
    Again, Python's new style formatting surpasses the old variant by providing more
    control over how values are padded and aligned.

    You are able to choose the padding character:
    """

    new_result = '{:_<10}'.format('test')
    rust_result = 'format!("{:_<10}", "test")'

    assert new_result == run_rust(rust_result)
    assert new_result == 'test______'  # output


def test_string_pad_align_4():
    """
    And also center align values:
    """

    new_result = '{:^10}'.format('test')
    rust_result = 'format!("{:^10}", "test")'

    assert new_result == run_rust(rust_result)
    assert new_result == '   test   '  # output


def test_string_truncating():
    """
    # Truncating long strings

    Inverse to padding it is also possible to truncate overly long values
    to a specific number of characters.

    The number behind a `.` in the format specifies the precision of the
    output. For strings that means that the output is truncated to the
    specified length. In our example this would be 5 characters.
    """
    old_result = '%.5s' % ('xylophone', )
    new_result = '{:.5}'.format('xylophone')
    rust_result = 'format!("{:.5}", "xylophone")'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == 'xylop'  # output


def test_string_truncate_2():
    """
    By argument:
    """
    old_result = '%.*s' % (7, 'xylophone', )
    new_result = '{:.{}}'.format('xylophone', 7)
    rust_result = 'format!("{:.1$}", "xylophone", 7)'
    # rust_result = 'format!("{:.*}", 7, "xylophone")'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == 'xylopho'  # output


def test_string_trunc_pad():
    """
    # Combining truncating and padding

    It is also possible to combine truncating and padding:
    """

    old_result = '%-10.5s' % ('xylophone', )
    new_result = '{:10.5}'.format('xylophone')
    rust_result = 'format!("{:10.5}", "xylophone")'

    assert old_result == new_result == run_rust(rust_result)
    assert new_result == 'xylop     '  # output


def test_number():
    """
    # Numbers

    Of course it is also possible to format numbers.

    Integers:
    """
    old_result = '%d' % (42, )
    new_result = '{:d}'.format(42)
    rust_result = 'format!("{}", 42)'     # FIXME

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == '42'  # output


def test_number_2():
    """
    Floats:
    """
    old_result = '%f' % (3.141592653589793, )
    new_result = '{:f}'.format(3.141592653589793)
    rust_result = 'format!("{:.6}", 3.141592653589793)'     # FIXME

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == '3.141593'  # output


def test_number_padding():
    """
    # Padding numbers

    Similar to strings numbers can also be constrained to a specific width.
    """
    old_result = '%4d' % (42, )
    new_result = '{:4d}'.format(42)
    rust_result = 'format!("{:4}", 42)'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == '  42'  # output


def test_number_padding_2():
    """
    Again similar to truncating strings the precision for floating point
    numbers limits the number of positions after the decimal point.

    For floating points the padding value represents the length of the complete
    output. In the example below we want our output to have at least 6
    characters with 2 after the decimal point.
    """
    old_result = '%06.2f' % (3.141592653589793, )
    new_result = '{:06.2f}'.format(3.141592653589793)
    rust_result = 'format!("{:06.2}", 3.141592653589793)'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == '003.14'  # output


def test_number_padding_3():
    """
    For integer values providing a precision doesn't make much sense and is
    actually forbidden in the Python's new style (it will result in a ValueError).
    """
    old_result = '%04d' % (42, )
    new_result = '{:04d}'.format(42)
    rust_result = 'format!("{:04}", 42)'

    with pytest.raises(ValueError):
        '{:04.2d}'.format(42)

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == '0042'  # output


def test_number_sign():
    """
    # Signed numbers

    By default only negative numbers are prefixed with a sign. This can be
    changed of course.
    """

    old_result = '%+d' % (42, )
    new_result = '{:+d}'.format(42)
    rust_result = 'format!("{:+}", 42)'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == '+42'  # output


def test_number_sign_2():
    """
    Use a space character to indicate that negative numbers should be prefixed
    with a minus symbol and a leading space should be used for positive ones.
    """
    old_result = '% d' % (-23, )
    new_result = '{: d}'.format(-23)
    # TODO

    assert old_result == new_result
    assert old_result == '-23'  # output


def test_number_sign_3():
    old_result = '% d' % (42, )
    new_result = '{: d}'.format(42)
    # TODO

    assert old_result == ' 42'  # output


def test_number_sign_4():
    """
    Python's new style formatting is also able to control the position of the sign
    symbol relative to the padding.
    """

    new_result = '{:=5d}'.format(-23)
    # TODO

    assert new_result == '-  23'  # output


def test_named_placeholders():
    """
    # Named placeholders

    Python's both formatting styles support named placeholders.
    """
    data = {
        'first': 'Hodor',
        'last': 'Hodor!',
    }

    old_result = '%(first)s %(last)s' % data
    new_result = '{first} {last}'.format(**data)
    rust_result = 'format!("{first} {last}", first="Hodor", last="Hodor!")'

    assert old_result == new_result == run_rust(rust_result)
    assert old_result == 'Hodor Hodor!'  # output


def test_named_placeholders_2():
    """
    `.format()` also accepts keyword arguments.
    """

    new_result = '{first} {last}'.format(first="Hodor", last="Hodor!")
    rust_result = 'format!("{first} {last}", first="Hodor", last="Hodor!")'

    assert new_result == run_rust(rust_result)
    assert new_result == 'Hodor Hodor!'  # output


def test_getitem_and_getattr():
    """
    # Getitem and Getattr

    Python's new style formatting allows even greater flexibility in accessing nested
    data structures.

    It supports accessing containers that support `__getitem__` like for
    example dictionaries and lists:

    """
    person = {
        'first': 'Jean-Luc',
        'last': 'Picard',
    }

    new_result = '{p[first]} {p[last]}'.format(p=person)
    # TODO

    assert new_result == 'Jean-Luc Picard'  # output


def test_getitem_and_getattr_2():
    data = [4, 8, 15, 16, 23, 42]

    new_result = '{d[4]} {d[5]}'.format(d=data)
    # TODO

    assert new_result == '23 42'  # output


def test_getitem_and_getattr_3():
    """
    As well as accessing attributes on objects via `getattr()`:
    """

    class Plant(object):
        type = "tree"

    new_result = '{p.type}'.format(p=Plant())
    # TODO

    assert new_result == 'tree'  # output


def test_getitem_and_getattr_4():
    """
    Both type of access can be freely mixed and arbitrarily nested:
    """

    class Plant(object):
        type = "tree"
        kinds = [{
            'name': "oak",
        }, {
            'name': "maple"
        }]

    new_result = '{p.type}: {p.kinds[0][name]}'.format(p=Plant())
    # TODO

    assert new_result == 'tree: oak'  # output


def test_datetime():
    """
    # Datetime

    Additionally Python's new style formatting allows objects to control their own
    rendering. This for example allows datetime objects to be formatted inline:
    """

    from datetime import datetime

    new_result = '{:%Y-%m-%d %H:%M}'.format(datetime(2001, 2, 3, 4, 5))
    # TODO

    assert new_result == '2001-02-03 04:05'  # output


def test_custom_1():
    """
    # Custom objects

    The above example works through the use of the `__format__()` magic method.
    You can define custom format handling in your own objects by overriding
    this method. This gives you complete control over the format syntax used.
    """

    class HAL9000(object):
        def __format__(self, format):
            if format == "open-the-pod-bay-doors":
                return "I'm afraid I can't do that."
            return "HAL 9000"

    new_result = '{:open-the-pod-bay-doors}'.format(HAL9000())
    # TODO

    assert new_result == "I'm afraid I can't do that."  # output
