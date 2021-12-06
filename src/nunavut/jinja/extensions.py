#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2021  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import typing

from nunavut.jinja.jinja2 import Environment, TemplateAssertionError, UndefinedError, nodes
from nunavut.jinja.jinja2.ext import Extension
from nunavut.jinja.jinja2.parser import Parser


class JinjaAssert(Extension):
    """
    Jinja2 extension that allows ``{% assert T.attribute %}`` statements. Templates should
    use these statements where False values would result in malformed source code :

        .. code-block:: python

            template = '''{% assert False %}'''

        .. invisible-code-block: python

            from nunavut.jinja.jinja2.exceptions import TemplateAssertionError
            from nunavut.jinja import CodeGenEnvironment
            from nunavut.jinja.jinja2 import DictLoader
            from nunavut.jinja.extensions import JinjaAssert

            e = CodeGenEnvironment(loader=DictLoader({'test': template}),
                                   extensions=[JinjaAssert])
            try:
                e.get_template('test').render()
                # huh. This should have raised a TemplateAssertionError
                assert False
            except TemplateAssertionError:
                pass

        This extension also support provding an assertion message:

        .. code-block:: python

            template = '''{% assert (1 + 1 == 4) and (2 + 2 == 5), "this was truly false" %}'''

        .. invisible-code-block: python

            e = CodeGenEnvironment(loader=DictLoader({'test': template}),
                                   extensions=[JinjaAssert])
            try:
                e.get_template('test').render()
                # huh. This should have raised a TemplateAssertionError
                assert False
            except TemplateAssertionError as e:
                assert e.message == 'this was truly false'

    """

    tags = set(["assert"])

    def __init__(self, environment: Environment):
        super().__init__(environment)

    def parse(self, parser: Parser) -> nodes.Node:
        """
        See http://jinja.pocoo.org/docs/2.10/extensions/ for help writing
        extensions.
        """

        # This will be the macro name "assert"
        token = next(parser.stream)

        # now we parse a single expression that must evaluate to True
        args = [
            parser.parse_expression(),
            nodes.Const(token.lineno),
            nodes.Const(parser.name),
            nodes.Const(parser.filename),
        ]

        if parser.stream.skip_if("comma"):
            args.append(parser.parse_expression())
        else:
            args.append(nodes.Const("Template assertion failed."))

        return nodes.CallBlock(self.call_method("_do_assert", args), [], [], "").set_lineno(token.lineno)

    def _do_assert(
        self, expression: str, lineno: int, name: str, filename: str, message: str, caller: typing.Callable
    ) -> typing.Any:
        if not expression:
            raise TemplateAssertionError(message, lineno, name, filename)
        return caller()


class UseQuery(Extension):
    """
    Jinja2 extension that allows conditional blocks like ``{% ifuses "std_variant" %}`` or
    ``{% ifnuses "std_variant" %}``. These are defined by the :class:`nunavut.lang.Language` object based on the values
    returned from :meth:`nunavut.lang.Language.get_uses_queries`.

        .. code-block:: python

            template  = ''' {%- ifuses "some_language_key" -%}
                                #include "header 0"
                            {%- elifuses "some_other_language_key" -%}
                                #include "header 1"
                            {%- else -%}
                                #include "header 2"
                            {%- endifuses -%}
                        '''

        .. invisible-code-block: python

            from nunavut.jinja.jinja2.exceptions import TemplateAssertionError
            from nunavut.jinja import CodeGenEnvironment
            from nunavut.jinja.jinja2 import DictLoader
            from nunavut.jinja.extensions import UseQuery
            from nunavut.lang import LanguageLoader
            from nunavut.jinja.jinja2 import UndefinedError
            from unittest.mock import MagicMock

            ln_c = LanguageLoader().load_language('c', True)

            lctx = MagicMock()
            lctx.get_supported_languages = MagicMock(return_value = {'c': ln_c})
            lctx.get_target_language = MagicMock(return_value = ln_c)


            e = CodeGenEnvironment(lctx=lctx,
                                   loader=DictLoader({'test': template}),
                                   extensions=[UseQuery])

            try:
                result = e.get_template('test').render()
                assert False
            except UndefinedError:
                pass

        For "not uses" replace all "uses" tokens with "nuses":

        .. code-block:: python

            template  = ''' {%- ifnuses "some_language_key" -%}
                                #include "header 1"
                            {%- elifnuses "some_other_language_key" -%}
                                #include "header 0"
                            {%- elifuses "yet_another_language_key" -%}
                                #include "header 2"
                            {%- else -%}
                                #include "header 3"
                            {%- endifnuses -%}
                        '''

    """

    tags = set(["ifuses", "ifnuses"])

    def __init__(self, environment: Environment):
        super().__init__(environment)

    def parse(self, parser: Parser) -> nodes.Node:
        """
        See http://jinja.pocoo.org/docs/2.10/extensions/ for help writing
        extensions.
        """

        if parser.stream.current.test("name:ifnuses"):
            negate = True
            ifname = "name:ifnuses"
        else:
            negate = False
            ifname = "name:ifuses"

        node = result = nodes.If(lineno=parser.stream.expect(ifname).lineno)
        while 1:
            args = [
                parser.parse_expression(),
                nodes.Const(parser.stream.current.lineno),
                nodes.Const(parser.name),
                nodes.Const(parser.filename),
            ]
            test_name = "_use_query" if not negate else "_use_nquery"
            node.test = self.call_method(test_name, args)
            node.body = parser.parse_statements(
                ("name:elifuses", "name:elifnuses", "name:else", "name:endifuses", "name:endifnuses")
            )
            node.elif_ = []
            node.else_ = []
            token = next(parser.stream)
            if token.test("name:elifuses"):
                negate = False
                node = nodes.If(lineno=parser.stream.current.lineno)
                result.elif_.append(node)
                continue
            elif token.test("name:elifnuses"):
                negate = True
                node = nodes.If(lineno=parser.stream.current.lineno)
                result.elif_.append(node)
                continue
            elif token.test("name:else"):
                result.else_ = parser.parse_statements(
                    (
                        "name:endifuses",
                        "name:endifnuses",
                    ),
                    drop_needle=True,
                )
            break
        return result

    def _use_query_common(self, uses_query_name: str, lineno: int, name: str, filename: str) -> bool:

        target_language = self.environment.target_language

        if target_language is None:
            raise TemplateAssertionError(
                "ifuses directive cannot be used in a language without a target language.", lineno, name, filename
            )
        if uses_query_name is None:
            raise TemplateAssertionError("Unknown uses_query_name found.", lineno, name, filename)

        try:
            uses_query = typing.cast(
                typing.Callable[..., bool], getattr(self.environment.target_language_uses_queries, uses_query_name)
            )
        except AttributeError:
            raise UndefinedError(
                'use query "{}" for language "{}" is not defined '
                "(line={}, name={}, filename={})".format(uses_query_name, target_language.name, lineno, name, filename)
            )

        return uses_query()

    def _use_nquery(self, uses_query_name: str, lineno: int, name: str, filename: str) -> bool:
        return not self._use_query_common(uses_query_name, lineno, name, filename)

    def _use_query(self, uses_query_name: str, lineno: int, name: str, filename: str) -> bool:
        return self._use_query_common(uses_query_name, lineno, name, filename)
