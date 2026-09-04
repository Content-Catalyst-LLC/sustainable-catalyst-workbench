# v5.2.0 Graph Mathematics Security Boundary

Interactive Graph Mathematics inherits the v5.1 restricted Python-expression AST parser. Only approved numeric operators, symbols, constants, and allow-listed mathematical functions are converted to SymPy expressions.

The graph layer does not accept imports, attributes, subscripts, lambdas, arbitrary function calls, Python statements, shell commands, filesystem paths, URLs, or executable callbacks. Graph parameter counts and all sample/grid dimensions are capped.

`arbitraryCodeExecutionAuthorized`, `pythonEvalAuthorized`, and `remoteShellAuthorized` remain false in status and graph objects.
