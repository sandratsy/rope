import unittest

import rope.base.oi
import rope.base.libutils
from ropetest import testutils


class DynamicOITest(unittest.TestCase):

    def setUp(self):
        super(DynamicOITest, self).setUp()
        self.project = testutils.sample_project(validate_objectdb=True)
        self.pycore = self.project.get_pycore()

    def tearDown(self):
        testutils.remove_project(self.project)
        super(DynamicOITest, self).tearDown()

    def test_simple_dti(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'def a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func(a_func)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        self.assertEquals(pymod.get_attribute('a_func').get_object(),
                          pymod.get_attribute('a_var').get_object())

    def test_module_dti(self):
        mod1 = self.pycore.create_module(self.project.root, 'mod1')
        mod2 = self.pycore.create_module(self.project.root, 'mod2')
        code = 'import mod1\ndef a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func(mod1)\n'
        mod2.write(code)
        self.pycore.run_module(mod2).wait_process()
        pymod2 = self.pycore.resource_to_pyobject(mod2)
        self.assertEquals(self.pycore.resource_to_pyobject(mod1),
                          pymod2.get_attribute('a_var').get_object())

    def test_class_from_another_module_dti(self):
        mod1 = self.pycore.create_module(self.project.root, 'mod1')
        mod2 = self.pycore.create_module(self.project.root, 'mod2')
        code1 = 'class AClass(object):\n    pass\n'
        code2 = 'from mod1 import AClass\n' \
               '\ndef a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func(AClass)\n'
        mod1.write(code1)
        mod2.write(code2)
        self.pycore.run_module(mod2).wait_process()
        pymod1 = self.pycore.resource_to_pyobject(mod1)
        pymod2 = self.pycore.resource_to_pyobject(mod2)
        self.assertEquals(pymod2.get_attribute('AClass').get_object(),
                          pymod2.get_attribute('a_var').get_object())


    def test_class_dti(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class AClass(object):\n    pass\n' \
               '\ndef a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func(AClass)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        self.assertEquals(pymod.get_attribute('AClass').get_object(),
                          pymod.get_attribute('a_var').get_object())

    def test_instance_dti(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class AClass(object):\n    pass\n' \
               '\ndef a_func(arg):\n    return eval("arg()")\n' \
               'a_var = a_func(AClass)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        self.assertEquals(pymod.get_attribute('AClass').get_object(),
                          pymod.get_attribute('a_var').get_object().get_type())

    def test_method_dti(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class AClass(object):\n    def a_method(self, arg):\n        return eval("arg()")\n' \
               'an_instance = AClass()\n' \
               'a_var = an_instance.a_method(AClass)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        self.assertEquals(pymod.get_attribute('AClass').get_object(),
                          pymod.get_attribute('a_var').get_object().get_type())

    def test_function_argument_dti(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'def a_func(arg):\n    pass\n' \
               'a_func(a_func)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pyscope = self.pycore.resource_to_pyobject(mod).get_scope()
        self.assertEquals(pyscope.get_name('a_func').get_object(),
                          pyscope.get_scopes()[0].get_name('arg').get_object())

    def test_classes_with_the_same_name(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'def a_func(arg):\n    class AClass(object):\n        pass\n    return eval("arg")\n' \
               'class AClass(object):\n    pass\n' \
               'a_var = a_func(AClass)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        self.assertEquals(pymod.get_attribute('AClass').get_object(),
                          pymod.get_attribute('a_var').get_object())

    def test_nested_classes(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'def a_func():\n    class AClass(object):\n        pass\n    return AClass\n' \
               'def another_func(arg):\n    return eval("arg")\n' \
               'a_var = another_func(a_func())\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pyscope = self.pycore.resource_to_pyobject(mod).get_scope()
        self.assertEquals(pyscope.get_scopes()[0].get_name('AClass').get_object(),
                          pyscope.get_name('a_var').get_object())

    def test_function_argument_dti2(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'def a_func(arg, a_builtin_type):\n    pass\n' \
               'a_func(a_func, [])\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pyscope = self.pycore.resource_to_pyobject(mod).get_scope()
        self.assertEquals(pyscope.get_name('a_func').get_object(),
                          pyscope.get_scopes()[0].get_name('arg').get_object())

    def test_dti_and_concluded_data_invalidation(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'def a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func(a_func)\n'
        mod.write(code)
        pymod = self.pycore.resource_to_pyobject(mod)
        pymod.get_attribute('a_var').get_object()
        self.pycore.run_module(mod).wait_process()
        self.assertEquals(pymod.get_attribute('a_func').get_object(),
                          pymod.get_attribute('a_var').get_object())

    def test_list_objects_and_dynamicoi(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C(object):\n    pass\ndef a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func([C()])[0]\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_for_loops_and_dynamicoi(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C(object):\n    pass\ndef a_func(arg):\n    return eval("arg")\n' \
               'for c in a_func([C()]):\n    a_var = c\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_dict_objects_and_dynamicoi(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C(object):\n    pass\n' \
               'def a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func({1: C()})[1]\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_dict_keys_and_dynamicoi(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C(object):\n    pass\n' \
               'def a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func({C(): 1}).keys()[0]\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_dict_keys_and_dynamicoi2(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'def a_func(arg):\n    return eval("arg")\n' \
               'a, b = a_func((C1(), C2()))\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_strs_and_dynamicoi(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'def a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func("hey")\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertTrue(isinstance(a_var.get_type(), rope.base.builtins.Str))

    def test_textual_transformations(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C(object):\n    pass\ndef f():\n    pass\na_var = C()\n' \
               'a_list = [C()]\na_str = "hey"\na_file = open("file.txt")\n'
        mod.write(code)
        to_pyobject = rope.base.oi.transform.TextualToPyObject(self.project)
        to_textual = rope.base.oi.transform.PyObjectToTextual(self.project)
        pymod = self.pycore.resource_to_pyobject(mod)
        def complex_to_textual(pyobject):
            return to_textual.transform(
                to_pyobject.transform(to_textual.transform(pyobject)))
        for name in ('C', 'f', 'a_var', 'a_list', 'a_str', 'a_file'):
            var = pymod.get_attribute(name).get_object()
            self.assertEquals(to_textual.transform(var), complex_to_textual(var))
        self.assertEquals(to_textual.transform(pymod), complex_to_textual(pymod))
        enumerate_func = rope.base.builtins.builtins['enumerate'].get_object()
        self.assertEquals(to_textual.transform(enumerate_func),
                          complex_to_textual(enumerate_func))

    def test_arguments_with_keywords(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'def a_func(arg):\n    return eval("arg")\n' \
               'a = a_func(arg=C1())\nb = a_func(arg=C2())\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_a_function_with_different_returns(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'def a_func(arg):\n    return eval("arg")\n' \
               'a = a_func(C1())\nb = a_func(C2())\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_a_function_with_different_returns2(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'def a_func(p):\n    if p == C1:\n        return C1()\n' \
               '    else:\n        return C2()\n' \
               'a = a_func(C1)\nb = a_func(C2)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_ignoring_star_args(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'def a_func(p, *args):\n    if p == C1:\n        return C1()\n' \
               '    else:\n        return C2()\n' \
               'a = a_func(C1, 1)\nb = a_func(C2, 2)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_ignoring_double_star_args(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'def a_func(p, *kwds, **args):\n    if p == C1:\n        return C1()\n' \
               '    else:\n        return C2()\n' \
               'a = a_func(C1, kwd=1)\nb = a_func(C2, kwd=2)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        pymod = self.pycore.resource_to_pyobject(mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_invalidating_data_after_changing(self):
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'def a_func(arg):\n    return eval("arg")\n' \
               'a_var = a_func(a_func)\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        mod.write(code.replace('a_func', 'newfunc'))
        mod.write(code)
        pymod = self.pycore.resource_to_pyobject(mod)
        self.assertNotEquals(pymod.get_attribute('a_func').get_object(),
                             pymod.get_attribute('a_var').get_object())

    def test_invalidating_data_after_moving(self):
        mod2 = self.pycore.create_module(self.project.root, 'mod2')
        mod2.write('class C(object):\n    pass\n')
        mod = self.pycore.create_module(self.project.root, 'mod')
        code = 'import mod2\ndef a_func(arg):\n    return eval(arg)\n' \
               'a_var = a_func("mod2.C")\n'
        mod.write(code)
        self.pycore.run_module(mod).wait_process()
        mod.move('newmod.py')
        pymod = self.pycore.get_module('newmod')
        pymod2 = self.pycore.resource_to_pyobject(mod2)
        self.assertEquals(pymod2.get_attribute('C').get_object(),
                          pymod.get_attribute('a_var').get_object())


class NewStaticOITest(unittest.TestCase):

    def setUp(self):
        super(NewStaticOITest, self).setUp()
        self.project = testutils.sample_project(validate_objectdb=True)
        self.pycore = self.project.get_pycore()
        self.mod = self.pycore.create_module(self.project.root, 'mod')

    def tearDown(self):
        testutils.remove_project(self.project)
        super(NewStaticOITest, self).tearDown()

    def test_static_oi_for_simple_function_calls(self):
        code = 'class C(object):\n    pass\ndef f(p):\n    pass\nf(C())\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        f_scope = pymod.get_attribute('f').get_object().get_scope()
        p_type = f_scope.get_name('p').get_object().get_type()
        self.assertEquals(c_class, p_type)

    def test_static_oi_not_failing_when_callin_callables(self):
        code = 'class C(object):\n    pass\nC()\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)

    def test_static_oi_for_nested_calls(self):
        code = 'class C(object):\n    pass\ndef f(p):\n    pass\n' \
               'def g(p):\n    return p\nf(g(C()))\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        f_scope = pymod.get_attribute('f').get_object().get_scope()
        p_type = f_scope.get_name('p').get_object().get_type()
        self.assertEquals(c_class, p_type)

    def test_static_oi_class_methods(self):
        code = 'class C(object):\n    def f(self, p):\n        pass\n' \
               'C().f(C())'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        f_scope = c_class.get_attribute('f').get_object().get_scope()
        p_type = f_scope.get_name('p').get_object().get_type()
        self.assertEquals(c_class, p_type)

    def test_static_oi_preventing_soi_maximum_recursion_exceptions(self):
        code = 'item = {}\nfor item in item.keys():\n    pass\n'
        self.mod.write(code)
        try:
            self.pycore.analyze_module(self.mod)
        except RuntimeError, e:
            self.fail(str(e))

    def test_static_oi_for_infering_returned_types_from_functions_based_on_parameters(self):
        code = 'class C(object):\n    pass\ndef func(p):\n    return p\n' \
               'a_var = func(C())\n'
        self.mod.write(code)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_a_function_with_different_returns(self):
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'def a_func(arg):\n    return arg\n' \
               'a = a_func(C1())\nb = a_func(C2())\n'
        self.mod.write(code)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_not_reporting_out_of_date_information(self):
        code = 'class C1(object):\n    pass\n' \
               'def f(arg):\n    return C1()\na_var = f('')\n'
        self.mod.write(code)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c1_class, a_var.get_type())

        self.mod.write(code.replace('C1', 'C2'))
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c2_class, a_var.get_type())

    def test_invalidating_concluded_data_in_a_function(self):
        mod1 = self.pycore.create_module(self.project.root, 'mod1')
        mod2 = self.pycore.create_module(self.project.root, 'mod2')
        mod1.write('def func(arg):\n    temp = arg\n    return temp\n')
        mod2.write('import mod1\n'
                   'class C1(object):\n    pass\n'
                   'class C2(object):\n    pass\n'
                   'a_var = mod1.func(C1())\n')
        pymod2 = self.pycore.resource_to_pyobject(mod2)
        c1_class = pymod2.get_attribute('C1').get_object()
        a_var = pymod2.get_attribute('a_var').get_object()
        self.assertEquals(c1_class, a_var.get_type())

        mod2.write(mod2.read()[:mod2.read().rfind('C1()')] + 'C2())\n')
        pymod2 = self.pycore.resource_to_pyobject(mod2)
        c2_class = pymod2.get_attribute('C2').get_object()
        a_var = pymod2.get_attribute('a_var').get_object()
        self.assertEquals(c2_class, a_var.get_type())

    def test_handling_generator_functions_for_strs(self):
        self.mod.write('class C(object):\n    pass\ndef f(p):\n    yield p()\n'
                       'for c in f(C):\n    a_var = c\n')
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    # TODO: Returning a generator for functions that yield unknowns
    def xxx_test_handling_generator_functions_when_unknown_type_is_yielded(self):
        self.mod.write('class C(object):\n    pass\ndef f():\n    yield eval("C()")\n'
                       'a_var = f()\n')
        pymod = self.pycore.resource_to_pyobject(self.mod)
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertTrue(isinstance(a_var.get_type(),
                                   rope.base.builtins.Generator))

    def test_static_oi_for_lists_depending_on_append_function(self):
        code = 'class C(object):\n    pass\nl = list()\n' \
               'l.append(C())\na_var = l.pop()\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_static_oi_for_lists_per_object_for_get_item(self):
        code = 'class C(object):\n    pass\nl = list()\n' \
               'l.append(C())\na_var = l[0]\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_static_oi_for_lists_per_object_for_fields(self):
        code = 'class C(object):\n    pass\n' \
               'class A(object):\n    def __init__(self):\n        self.l = []\n' \
               '    def set(self):\n        self.l.append(C())\n' \
               'a = A()\na.set()\na_var = a.l[0]\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_static_oi_for_lists_per_object_for_set_item(self):
        code = 'class C(object):\n    pass\nl = [None]\n' \
               'l[0] = C()\na_var = l[0]\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_static_oi_for_lists_per_object_for_extending_lists(self):
        code = 'class C(object):\n    pass\nl = []\n' \
               'l.append(C())\nl2 = []\nl2.extend(l)\na_var = l2[0]\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_static_oi_for_lists_per_object_for_iters(self):
        code = 'class C(object):\n    pass\nl = []\n' \
               'l.append(C())\nfor c in l:\n    a_var = c\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_static_oi_for_dicts_depending_on_append_function(self):
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'd = {}\nd[C1()] = C2()\na, b = d.popitem()\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_static_oi_for_dicts_depending_on_for_loops(self):
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'd = {}\nd[C1()] = C2()\nfor k, v in d.items():\n    a = k\n    b = v\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_static_oi_for_dicts_depending_on_update(self):
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'd = {}\nd[C1()] = C2()\nd2 = {}\nd2.update(d)\na, b = d2.popitem()\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_static_oi_for_dicts_depending_on_update_on_seqs(self):
        code = 'class C1(object):\n    pass\nclass C2(object):\n    pass\n' \
               'd = {}\nd.update([(C1(), C2())])\na, b = d.popitem()\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        c2_class = pymod.get_attribute('C2').get_object()
        a_var = pymod.get_attribute('a').get_object()
        b_var = pymod.get_attribute('b').get_object()
        self.assertEquals(c1_class, a_var.get_type())
        self.assertEquals(c2_class, b_var.get_type())

    def test_static_oi_for_sets_per_object_for_set_item(self):
        code = 'class C(object):\n    pass\ns = set()\n' \
               's.add(C())\na_var = s.pop() \n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c_class, a_var.get_type())

    def test_properties_and_calling_get_property(self):
        code = 'class C1(object):\n    pass\n' \
               'class C2(object):\n    c1 = C1()\n' \
               '    def get_c1(self):\n        return self.c1\n' \
               '    p = property(get_c1)\nc2 = C2()\na_var = c2.p\n'
        self.mod.write(code)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c1_class, a_var.get_type())

    def test_soi_on_constructors(self):
        code = 'class C1(object):\n    pass\n' \
               'class C2(object):\n' \
               '    def __init__(self, arg):\n        self.attr = arg\n' \
               'c2 = C2(C1())\na_var = c2.attr'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        a_var = pymod.get_attribute('a_var').get_object()
        self.assertEquals(c1_class, a_var.get_type())

    def test_not_saving_unknown_function_returns(self):
        mod2 = self.pycore.create_module(self.project.root, 'mod2')
        self.mod.write('class C(object):\n    pass\nl = []\nl.append(C())\n')
        mod2.write('import mod\ndef f():\n    return mod.l.pop()\na_var = f()\n')
        pymod = self.pycore.resource_to_pyobject(self.mod)
        pymod2 = self.pycore.resource_to_pyobject(mod2)
        c_class = pymod.get_attribute('C').get_object()
        a_var = pymod2.get_attribute('a_var')

        self.pycore.analyze_module(mod2)
        self.assertNotEquals(c_class, a_var.get_object().get_type())

        self.pycore.analyze_module(self.mod)
        self.assertEquals(c_class, a_var.get_object().get_type())

    def test_using_the_best_callinfo(self):
        code = 'class C1(object):\n    pass\n' \
               'def f(arg1, arg2, arg3):\n    pass\n' \
               'f("", None, C1())\nf("", C1(), None)\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c1_class = pymod.get_attribute('C1').get_object()
        f_scope = pymod.get_attribute('f').get_object().get_scope()
        arg2 = f_scope.get_name('arg2').get_object()
        self.assertEquals(c1_class, arg2.get_type())

    def test_call_function_and_parameters(self):
        code = 'class A(object):\n    def __call__(self, p):\n        pass\n' \
               'A()("")\n'
        self.mod.write(code)
        self.pycore.analyze_module(self.mod)
        scope = self.pycore.resource_to_pyobject(self.mod).get_scope()
        p_object = scope.get_scopes()[0].get_scopes()[0].\
                   get_name('p').get_object()
        self.assertTrue(isinstance(p_object.get_type(),
                                   rope.base.builtins.Str))

    def test_report_change_in_libutils(self):
        code = 'class C(object):\n    pass\ndef f(p):\n    pass\nf(C())\n'
        mod_file = open(self.mod.real_path, 'w')
        mod_file.write(code)
        mod_file.close()
        rope.base.libutils.report_change(self.project, self.mod.real_path, '')
        pymod = self.pycore.resource_to_pyobject(self.mod)
        c_class = pymod.get_attribute('C').get_object()
        f_scope = pymod.get_attribute('f').get_object().get_scope()
        p_type = f_scope.get_name('p').get_object().get_type()
        self.assertEquals(c_class, p_type)


def suite():
    result = unittest.TestSuite()
    result.addTests(unittest.makeSuite(DynamicOITest))
    result.addTests(unittest.makeSuite(NewStaticOITest))
    return result


if __name__ == '__main__':
    unittest.main()
