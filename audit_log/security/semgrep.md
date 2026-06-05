               
               
┌─────────────┐
│ Scan Status │
└─────────────┘
  Scanning 13141 files tracked by git with 1059 Code rules:
                                                                                
  Language      Rules   Files          Origin      Rules                        
 ─────────────────────────────        ───────────────────                       
  <multilang>      60   18756          Community    1059                        
  python          243    3473                                                   
  c                 5      44                                                   
  json              4      34                                                   
  yaml             31      29                                                   
  js              153      15                                                   
  bash              4       2                                                   
  dockerfile        6       1                                                   
  html              1       1                                                   
                                                                                
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_openedge_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pip/_vendor/pygments/lexers/_mapping.py when running
the following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_lilypond_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_lasso_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_scheme_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/packaging/licenses/_spdx.py when running the following
rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 3 timeout error(s) in venv/lib/python3.12/site-
packages/emerge/output/html/vendors/bootstrap/js/bootstrap.bundle.js when running the following rules: [javascript.aws-
lambda.security.pg-sqli.pg-sqli, javascript.aws-lambda.security.tainted-eval.tainted-eval, javascript.aws-
lambda.security.tainted-html-string.tainted-html-string]
Semgrep stopped running rules on venv/lib/python3.12/site-
packages/emerge/output/html/vendors/bootstrap/js/bootstrap.bundle.js after 3 timeout error(s). See `--timeout-threshold`
for more info.
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_asy_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/ncl.py when running the following
rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_vim_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_sourcemod_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/matlab.py when running the following
rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_scilab_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_mapping.py when running the following
rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_cocoa_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/lisp.py when running the following
rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pip/_vendor/idna/uts46data.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pygments/lexers/_stata_builtins.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
Warning: 1 timeout error(s) in venv/lib/python3.12/site-packages/pip/_vendor/rich/_emoji_codes.py when running the
following rules: [python.boto3.security.hardcoded-token.hardcoded-token]
                     
                     
┌───────────────────┐
│ 241 Code Findings │
└───────────────────┘
            
    main.py 
       python.fastapi.security.wildcard-cors.wildcard-cors                      
          CORS policy allows any origin (using wildcard '*'). This is insecure  
  and should be avoided.                                                        
          Details: https://sg.run/KxApY                                         
                                                                                
           76┆ allow_origins=["*"],
                       
    venv/bin/get_gprof 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
           43┆ exec(line)
            ⋮┆----------------------------------------
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
           46┆ obj = eval(obj[-1])
                          
    venv/bin/get_objgraph 
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
           28┆ load_types(pickleable=True,unpickleable=True)
            ⋮┆----------------------------------------
           44┆ obj = pickle.load(open(objtype,'rb'))
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
           44┆ obj = pickle.load(open(objtype,'rb'))
                    
    venv/bin/undill 
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
           21┆ print (dill.load(open(file,'rb')))
                                                          
    venv/lib/python3.12/site-packages/astroid/__init__.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          230┆ if (val := globals().get(f"_DEPRECATED_{name}")) is None:
                                                          
    venv/lib/python3.12/site-packages/astroid/modutils.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          178┆ module = importlib.import_module(dotted_name)
                                                    
    venv/lib/python3.12/site-packages/attr/_make.py 
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
          227┆ eval(bytecode, globs, locs)
            ⋮┆----------------------------------------
       python.lang.security.audit.dangerous-annotations-usage.dangerous-annotati
  ons-usage                                                                     
          Annotations passed to `typing.get_type_hints` are evaluated in        
  `globals` and `locals`                                                        
          namespaces. Make sure that no arbitrary value can be written as the   
  annotation and passed to                                                      
          `typing.get_type_hints` function.                                     
          Details: https://sg.run/8R6J                                          
                                                                                
         3140┆ self.__call__.__annotations__["return"] = rt
            ⋮┆----------------------------------------
         3393┆ pipe_converter.__annotations__["val"] = t
            ⋮┆----------------------------------------
         3402┆ pipe_converter.__annotations__["return"] = rt
                                                         
    venv/lib/python3.12/site-packages/attr/converters.py 
       python.lang.security.audit.dangerous-annotations-usage.dangerous-annotati
  ons-usage                                                                     
          Annotations passed to `typing.get_type_hints` are evaluated in        
  `globals` and `locals`                                                        
          namespaces. Make sure that no arbitrary value can be written as the   
  annotation and passed to                                                      
          `typing.get_type_hints` function.                                     
          Details: https://sg.run/8R6J                                          
                                                                                
           54┆ optional_converter.__annotations__["val"] = typing.Optional[t]
            ⋮┆----------------------------------------
           58┆ optional_converter.__annotations__["return"] =                   
  typing.Optional[rt]                                                           
                                                            
    venv/lib/python3.12/site-packages/click/_termui_impl.py 
       python.lang.compatibility.python36.python36-compatibility-Popen1  
          the `errors` argument to Popen is only available on Python 3.6+
          Details: https://sg.run/weBP                                   
                                                                         
          510┆ c = subprocess.Popen(
          511┆     [str(cmd_path)] + cmd_params,
          512┆     shell=False,
          513┆     stdin=subprocess.PIPE,
          514┆     env=env,
          515┆     errors="replace",
          516┆     text=True,
          517┆ )
                                                      
    venv/lib/python3.12/site-packages/click/parser.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          520┆ return globals()[f"_{name}"]
                                                    
    venv/lib/python3.12/site-packages/dill/_dill.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          422┆ raise PicklingError(msg)
            ⋮┆----------------------------------------
       python.lang.security.audit.marshal.marshal-usage                         
          The marshal module is not intended to be secure against erroneous or  
  maliciously constructed                                                       
          data. Never unmarshal data received from an untrusted or              
  unauthenticated source. See more                                              
          details:                                                              
  https://docs.python.org/3/library/marshal.html?highlight=security             
          Details: https://sg.run/3xor                                          
                                                                                
          596┆ return marshal.loads(string)
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          893┆ raise UnpicklingError(err)
            ⋮┆----------------------------------------
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
          980┆ return eval(repr_str)
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
         1027┆ raise UnpicklingError("%s object exists at %s but a PyCapsule    
  object was expected." % (type(capsule), name))                                
            ⋮┆----------------------------------------
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
         1038┆ return eval(attr+'.__dict__["'+name+'"]')
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
         1796┆ raise PicklingError("Cannot find registry of ABC %s", obj)
                                                       
    venv/lib/python3.12/site-packages/dill/_objects.py 
       python.lang.security.deserialization.pickle.avoid-shelve                 
          Avoid using `shelve`, which uses `pickle`, which is known to lead to  
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/dKkZ                                          
                                                                                
          311┆ a['ShelveType'] = shelve.Shelf({})
                                                     
    venv/lib/python3.12/site-packages/dill/_shims.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          174┆ func = globals().get(name)
                                                     
    venv/lib/python3.12/site-packages/dill/detect.py 
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
          245┆ if pickles(obj,exact,safe): return None
            ⋮┆----------------------------------------
          248┆ for attr in dir(obj) if not                                      
  pickles(getattr(obj,attr),exact,safe)))                                       
            ⋮┆----------------------------------------
          254┆ if pickles(obj,exact,safe): return None
            ⋮┆----------------------------------------
          257┆ for attr in dir(obj) if not                                      
  pickles(getattr(obj,attr),exact,safe)))                                       
            ⋮┆----------------------------------------
          264┆ pik = copy(obj)
            ⋮┆----------------------------------------
          282┆ if not pickles(_attr,exact,safe):
                                                       
    venv/lib/python3.12/site-packages/dill/objtypes.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
           18┆ exec("%s = type(objects['%s'])" % (_type,_type))
                                                      
    venv/lib/python3.12/site-packages/dill/session.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          226┆ if locals()[par]:  # the defaults are None and False
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
          247┆ pickler = Pickler(file, protocol, **kwds)
            ⋮┆----------------------------------------
          448┆ unpickler = Unpickler(file, **kwds)
            ⋮┆----------------------------------------
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          611┆ setattr(_dill, name, globals()[name])
                                                     
    venv/lib/python3.12/site-packages/dill/source.py 
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
           60┆ _ = eval("lambda %s : %s" % (lhs,rhs), globals(),locals())
            ⋮┆----------------------------------------
           82┆ _f = eval("lambda %s : %s" % (_lhs,_rhs), globals(),locals())
            ⋮┆----------------------------------------
          397┆ obj = eval(lines[0].lstrip(name + ' = '))
            ⋮┆----------------------------------------
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          543┆ exec(getimportable(f, alias='_'), __globals__, __locals__)
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
          575┆ pik = repr(dumps(object))
            ⋮┆----------------------------------------
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          713┆ try: exec(_str) #XXX: check if == obj? (name collision)
                                                   
    venv/lib/python3.12/site-packages/dill/temp.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
           71┆ exec(source, local)
            ⋮┆----------------------------------------
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
           72┆ _ = eval("%s" % alias, local)
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
          133┆ return pickle.load(open(name, mode=mode, **kwds))
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          133┆ return pickle.load(open(name, mode=mode, **kwds))
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
          163┆ pickle.dump(object, file)
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          163┆ pickle.dump(object, file)
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
          180┆ return pickle.load(StringIO(value))
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          180┆ return pickle.load(StringIO(value))
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
          193┆ pickle.dump(object, file)
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          193┆ pickle.dump(object, file)
            ⋮┆----------------------------------------
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          220┆ exec(source, local)
            ⋮┆----------------------------------------
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
          221┆ _ = eval("%s" % alias, local)
                                                                                
    venv/lib/python3.12/site-packages/emerge/output/html/vendors/bootstrap/js/bo
  otstrap.esm.js                                                                
       javascript.lang.security.audit.detect-non-literal-regexp.detect-non-liter
  al-regexp                                                                     
          RegExp() called with a `configTypes` function argument, this might    
  allow an attacker to                                                          
          cause a Regular Expression Denial-of-Service (ReDoS) within your      
  application as RegExP                                                         
          blocks the main thread. For this reason, it is recommended to use     
  hardcoded regexes instead.                                                    
          If your regex is run on user-controlled input, consider performing    
  input validation or use a                                                     
          regex checking/sanitization library such as                           
  https://www.npmjs.com/package/recheck to verify                               
          that the regex does not appear vulnerable to ReDoS.                   
          Details: https://sg.run/gr65                                          
                                                                                
          767┆ if (!new RegExp(expectedTypes).test(valueType)) {
                                                                                
    venv/lib/python3.12/site-packages/emerge/output/html/vendors/bootstrap/js/bo
  otstrap.js                                                                    
       javascript.lang.security.audit.detect-non-literal-regexp.detect-non-liter
  al-regexp                                                                     
          RegExp() called with a `configTypes` function argument, this might    
  allow an attacker to                                                          
          cause a Regular Expression Denial-of-Service (ReDoS) within your      
  application as RegExP                                                         
          blocks the main thread. For this reason, it is recommended to use     
  hardcoded regexes instead.                                                    
          If your regex is run on user-controlled input, consider performing    
  input validation or use a                                                     
          regex checking/sanitization library such as                           
  https://www.npmjs.com/package/recheck to verify                               
          that the regex does not appear vulnerable to ReDoS.                   
          Details: https://sg.run/gr65                                          
                                                                                
          791┆ if (!new RegExp(expectedTypes).test(valueType)) {
                                                      
    venv/lib/python3.12/site-packages/git/__init__.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          192┆ return importlib.import_module(fullname)
                                                                    
    venv/lib/python3.12/site-packages/git/objects/submodule/base.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
         1482┆ setattr(self, attr, loc[attr])
                                                  
    venv/lib/python3.12/site-packages/git/util.py 
       python.lang.security.audit.insecure-file-permissions.insecure-file-permis
  sions                                                                         
          These permissions `0o777` are widely permissive and grant access to   
  more people than may be                                                       
          necessary. A good default is `0o644` which gives read and write access
  to yourself and read                                                          
          access to everyone else.                                              
          Details: https://sg.run/AXY4                                          
                                                                                
          250┆ os.chmod(path, 0o777)
                                                    
    venv/lib/python3.12/site-packages/gitdb/util.py 
       python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha
  1                                                                             
          Detected SHA1 hash algorithm which is considered insecure. SHA1 is not
  collision resistant                                                           
          and is therefore not suitable as a cryptographic signature. Use SHA256
  or SHA3 instead.                                                              
          Details: https://sg.run/ydYx                                          
                                                                                
           ▶▶┆ Autofix ▶ hashlib.sha256(source)
          139┆ return hashlib.sha1(source)
                                                                   
    venv/lib/python3.12/site-packages/humanfriendly/deprecation.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          250┆ module = importlib.import_module(module_name)
                                                               
    venv/lib/python3.12/site-packages/humanfriendly/testing.py 
       python.lang.security.audit.insecure-file-permissions.insecure-file-permis
  sions                                                                         
          These permissions `0o755` are widely permissive and grant access to   
  more people than may be                                                       
          necessary. A good default is `0o644` which gives read and write access
  to yourself and read                                                          
          access to everyone else.                                              
          Details: https://sg.run/AXY4                                          
                                                                                
          528┆ os.chmod(pathname, 0o755)
                                                             
    venv/lib/python3.12/site-packages/humanfriendly/usage.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          299┆ usage_text = import_module(module_name).__doc__
                                                               
    venv/lib/python3.12/site-packages/interrogate/badge_gen.py 
       python.lang.compatibility.python37.python37-compatibility-importlib2     
          Found 'importlib.resources', which is a module only available on      
  Python 3.7+. This does not                                                    
          work in lower versions, and therefore is not backwards compatible. Use
  importlib_resources                                                           
          instead for older Python versions.                                    
          Details: https://sg.run/eL3y                                          
                                                                                
           10┆ from importlib import resources
                                                                    
    venv/lib/python3.12/site-packages/joblib/_memmapping_reducer.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          357┆ return (loads, (dumps(np.asarray(a),                             
  protocol=HIGHEST_PROTOCOL),))                                                 
            ⋮┆----------------------------------------
          528┆ return (loads, (dumps(a, protocol=HIGHEST_PROTOCOL),))
            ⋮┆----------------------------------------
          642┆ pool_module_name = whichmodule(delete_folder, "delete_folder")
                                                                                
    venv/lib/python3.12/site-packages/joblib/externals/cloudpickle/cloudpickle.p
  y                                                                             
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          197┆ return _pickle_getattribute(obj, name.split('.'))
            ⋮┆----------------------------------------
          200┆ return _pickle_getattribute(obj, name)[0]
            ⋮┆----------------------------------------
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          728┆ f_globals = {k: func.__globals__[k] for k in f_globals_ref if k  
  in func.__globals__}                                                          
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          972┆ raise pickle.PicklingError(
          973┆     "Cannot pickle files that are not opened for reading: %s" %  
  obj.mode                                                                      
          974┆ )
            ⋮┆----------------------------------------
          987┆ raise pickle.PicklingError(
          988┆     "Cannot pickle file %s as it cannot be read" % name
          989┆ ) from e
                                                                                
    venv/lib/python3.12/site-packages/joblib/externals/loky/backend/popen_loky_p
  osix.py                                                                       
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          174┆ prep_data = pickle.load(from_parent)
            ⋮┆----------------------------------------
          176┆ process_obj = pickle.load(from_parent)
                                                                                
    venv/lib/python3.12/site-packages/joblib/externals/loky/backend/popen_loky_w
  in32.py                                                                       
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          166┆ preparation_data = load(from_parent)
            ⋮┆----------------------------------------
          168┆ self = load(from_parent)
                                                                                
    venv/lib/python3.12/site-packages/joblib/externals/loky/backend/reduction.py
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          115┆ module_pickle = import_module(loky_pickler)
                                                        
    venv/lib/python3.12/site-packages/joblib/hashing.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          242┆ self._hash.update(pickle.dumps(obj))
                                                             
    venv/lib/python3.12/site-packages/joblib/numpy_pickle.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          131┆ pickle.dump(array, pickler.file_handle, protocol=5)
            ⋮┆----------------------------------------
          175┆ array = pickle.load(unpickler.file_handle)
                                                
    venv/lib/python3.12/site-packages/lizard.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
         1087┆ im('lizard_ext.lizard' + name.lower())
                                                                    
    venv/lib/python3.12/site-packages/narwhals/_spark_like/utils.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          234┆ return                                                           
  import_module(f"sqlframe.{_BaseSession().execution_dialect_name}.functions")  
            ⋮┆----------------------------------------
          248┆ return                                                           
  import_module(f"sqlframe.{_BaseSession().execution_dialect_name}.types")      
            ⋮┆----------------------------------------
          263┆ return import_module(
          264┆     f"sqlframe.{_BaseSession().execution_dialect_name}.window"
          265┆ ).Window
                                                         
    venv/lib/python3.12/site-packages/narwhals/_utils.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          630┆ return import_module(module_name)
                                                                   
    venv/lib/python3.12/site-packages/networkx/generators/atlas.py 
       python.lang.compatibility.python37.python37-compatibility-importlib2     
          Found 'importlib.resources', which is a module only available on      
  Python 3.7+. This does not                                                    
          work in lower versions, and therefore is not backwards compatible. Use
  importlib_resources                                                           
          instead for older Python versions.                                    
          Details: https://sg.run/eL3y                                          
                                                                                
            6┆ import importlib.resources
                                                               
    venv/lib/python3.12/site-packages/networkx/lazy_imports.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           65┆ return importlib.import_module(f"{module_name}.{name}")
            ⋮┆----------------------------------------
           67┆ submod =                                                         
  importlib.import_module(f"{module_name}.{attr_to_modules[name]}")             
                                                                   
    venv/lib/python3.12/site-packages/networkx/utils/decorators.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          912┆ exec(compiled, globl, locl)
                                                              
    venv/lib/python3.12/site-packages/numpy/_core/_methods.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          244┆ pickle.dump(self, f, protocol=protocol)
            ⋮┆----------------------------------------
          247┆ return pickle.dumps(self, protocol=protocol)
                                                                
    venv/lib/python3.12/site-packages/numpy/_core/multiarray.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          100┆ ufunc = namespace_names[ufunc_name]
                                                             
    venv/lib/python3.12/site-packages/numpy/f2py/auxfuncs.py 
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
          632┆ return eval(f"{l1}:{' and '.join(l2)}")
            ⋮┆----------------------------------------
          640┆ return eval(f"{l1}:{' or '.join(l2)}")
                                                              
    venv/lib/python3.12/site-packages/numpy/f2py/capi_maps.py 
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
          159┆ d = eval(f.read().lower(), {}, {})
            ⋮┆----------------------------------------
          296┆ ret['size'] = repr(eval(ret['size']))
            ⋮┆----------------------------------------
          449┆ v = eval(v, {}, {})
                                                                 
    venv/lib/python3.12/site-packages/numpy/f2py/crackfortran.py 
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
         1328┆ v = eval(initexpr, {}, params)
            ⋮┆----------------------------------------
         2270┆ r = eval(e, g, l)
            ⋮┆----------------------------------------
         2558┆ value = eval(value, {}, params)
            ⋮┆----------------------------------------
         2636┆ l = str(eval(l, {}, params))
            ⋮┆----------------------------------------
         2645┆ l = str(eval(l, {}, params))
            ⋮┆----------------------------------------
         2913┆ kindselect['kind'] = eval(
         2914┆     kindselect['kind'], {}, params)
            ⋮┆----------------------------------------
         2984┆ p = eval(v, g_params, params)
            ⋮┆----------------------------------------
         3015┆ item = eval(item, g_params, params)
            ⋮┆----------------------------------------
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
         3344┆ f = globals()[f'isintent_{intent}']
            ⋮┆----------------------------------------
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
         3467┆ v = eval(v)
                                                               
    venv/lib/python3.12/site-packages/numpy/lib/_datasource.py 
       python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use
  -detected                                                                     
          Detected a dynamic value being used with urllib. urllib supports      
  'file://' schemes, so a                                                       
          dynamic value controlled by a malicious actor may allow them to read  
  arbitrary files. Audit                                                        
          uses of urllib calls to ensure user data cannot control the URLs, or  
  consider using the                                                            
          'requests' library instead.                                           
          Details: https://sg.run/dKZZ                                          
                                                                                
          333┆ with urlopen(path) as openedurl:
            ⋮┆----------------------------------------
          475┆ netfile = urlopen(path)
                                                                
    venv/lib/python3.12/site-packages/numpy/lib/_format_impl.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          762┆ pickle.dump(array, fp, protocol=4, **pickle_kwargs)
            ⋮┆----------------------------------------
          838┆ array = pickle.load(fp, **pickle_kwargs)
                                                               
    venv/lib/python3.12/site-packages/numpy/lib/_npyio_impl.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
          494┆ return pickle.load(fid, **pickle_kwargs)
            ⋮┆----------------------------------------
          496┆ raise pickle.UnpicklingError(
          497┆     f"Failed to interpret file {file!r} as a pickle") from e
                                                                      
    venv/lib/python3.12/site-packages/numpy/testing/_private/utils.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
         1346┆ exec(astr, dict)
            ⋮┆----------------------------------------
         1632┆ exec(code, globs, locs)
                                                               
    venv/lib/python3.12/site-packages/numpy/typing/__init__.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          219┆ return globals()[name]
                                                             
    venv/lib/python3.12/site-packages/pip/_internal/cache.py 
       python.lang.security.audit.sha224-hash.sha224-hash                       
          This code uses a 224-bit hash function, which is deprecated or        
  disallowed in some security                                                   
          policies. Consider updating to a stronger hash function such as       
  SHA-384 or higher to ensure                                                   
          compliance and security.                                              
          Details: https://sg.run/Db1Yv                                         
                                                                                
           29┆ return hashlib.sha224(s.encode("ascii")).hexdigest()
                                                                         
    venv/lib/python3.12/site-packages/pip/_internal/commands/__init__.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          114┆ module = importlib.import_module(module_path)
                                                                              
    venv/lib/python3.12/site-packages/pip/_internal/commands/configuration.py 
       python.lang.security.audit.subprocess-shell-true.subprocess-shell-true   
          Found 'subprocess' function 'check_call' with 'shell=True'. This is   
  dangerous because this                                                        
          call will spawn the command using a shell process. Doing so propagates
  current shell                                                                 
          settings and variables, which makes it much easier for a malicious    
  actor to execute                                                              
          commands. Use 'shell=False' instead.                                  
          Details: https://sg.run/J92w                                          
                                                                                
           ▶▶┆ Autofix ▶ False
          239┆ subprocess.check_call(f'{editor} "{fname}"', shell=True)
                                                                      
    venv/lib/python3.12/site-packages/pip/_internal/commands/debug.py 
       python.lang.compatibility.python37.python37-compatibility-importlib2     
          Found 'importlib.resources', which is a module only available on      
  Python 3.7+. This does not                                                    
          work in lower versions, and therefore is not backwards compatible. Use
  importlib_resources                                                           
          instead for older Python versions.                                    
          Details: https://sg.run/eL3y                                          
                                                                                
            1┆ import importlib.resources
                                                                       
    venv/lib/python3.12/site-packages/pip/_internal/commands/search.py 
       python.lang.security.use-defused-xmlrpc.use-defused-xmlrpc               
          Detected use of xmlrpc. xmlrpc is not inherently safe from            
  vulnerabilities. Use                                                          
          defusedxml.xmlrpc instead.                                            
          Details: https://sg.run/weqY                                          
                                                                                
            5┆ import xmlrpc.client
                                                                    
    venv/lib/python3.12/site-packages/pip/_internal/network/auth.py 
       python.lang.security.audit.logging.logger-credential-leak.python-logger-c
  redential-disclosure                                                          
          Detected a python logger call with a potential hardcoded secret       
  "Getting credentials from                                                     
          keyring for %s" being logged. This may lead to secret credentials     
  being exposed. Make sure                                                      
          that the logger is not logging  sensitive information.                
          Details: https://sg.run/ydNx                                          
                                                                                
           85┆ logger.debug("Getting credentials from keyring for %s", url)
            ⋮┆----------------------------------------
       python.lang.security.audit.logging.logger-credential-leak.python-logger-c
  redential-disclosure                                                          
          Detected a python logger call with a potential hardcoded secret       
  "Getting password from                                                        
          keyring for %s" being logged. This may lead to secret credentials     
  being exposed. Make sure                                                      
          that the logger is not logging  sensitive information.                
          Details: https://sg.run/ydNx                                          
                                                                                
           92┆ logger.debug("Getting password from keyring for %s", url)
            ⋮┆----------------------------------------
       python.lang.security.audit.logging.logger-credential-leak.python-logger-c
  redential-disclosure                                                          
          Detected a python logger call with a potential hardcoded secret "Found
  credentials in url                                                            
          for %s" being logged. This may lead to secret credentials being       
  exposed. Make sure that the                                                   
          logger is not logging  sensitive information.                         
          Details: https://sg.run/ydNx                                          
                                                                                
          346┆ logger.debug("Found credentials in url for %s", netloc)
            ⋮┆----------------------------------------
       python.lang.security.audit.logging.logger-credential-leak.python-logger-c
  redential-disclosure                                                          
          Detected a python logger call with a potential hardcoded secret "Found
  credentials in index                                                          
          url for %s" being logged. This may lead to secret credentials being   
  exposed. Make sure that                                                       
          the logger is not logging  sensitive information.                     
          Details: https://sg.run/ydNx                                          
                                                                                
          362┆ logger.debug("Found credentials in index url for %s", netloc)
            ⋮┆----------------------------------------
       python.lang.security.audit.logging.logger-credential-leak.python-logger-c
  redential-disclosure                                                          
          Detected a python logger call with a potential hardcoded secret "Found
  credentials in netrc                                                          
          for %s" being logged. This may lead to secret credentials being       
  exposed. Make sure that the                                                   
          logger is not logging  sensitive information.                         
          Details: https://sg.run/ydNx                                          
                                                                                
          369┆ logger.debug("Found credentials in netrc for %s", netloc)
            ⋮┆----------------------------------------
       python.lang.security.audit.logging.logger-credential-leak.python-logger-c
  redential-disclosure                                                          
          Detected a python logger call with a potential hardcoded secret "Found
  credentials in                                                                
          keyring for %s" being logged. This may lead to secret credentials     
  being exposed. Make sure                                                      
          that the logger is not logging  sensitive information.                
          Details: https://sg.run/ydNx                                          
                                                                                
          382┆ logger.debug("Found credentials in keyring for %s", netloc)
            ⋮┆----------------------------------------
       python.lang.security.audit.logging.logger-credential-leak.python-logger-c
  redential-disclosure                                                          
          Detected a python logger call with a potential hardcoded secret "401  
  Error, Credentials not                                                        
          correct for %s" being logged. This may lead to secret credentials     
  being exposed. Make sure                                                      
          that the logger is not logging  sensitive information.                
          Details: https://sg.run/ydNx                                          
                                                                                
          541┆ logger.warning(
          542┆     "401 Error, Credentials not correct for %s",
          543┆     resp.request.url,
          544┆ )
                                                                      
    venv/lib/python3.12/site-packages/pip/_internal/network/xmlrpc.py 
       python.lang.security.use-defused-xmlrpc.use-defused-xmlrpc               
          Detected use of xmlrpc. xmlrpc is not inherently safe from            
  vulnerabilities. Use                                                          
          defusedxml.xmlrpc instead.                                            
          Details: https://sg.run/weqY                                          
                                                                                
            6┆ import xmlrpc.client
            ⋮┆----------------------------------------
           14┆ from xmlrpc.client import _HostType, _Marshallable
                                                                           
    venv/lib/python3.12/site-packages/pip/_internal/self_outdated_check.py 
       python.lang.security.audit.sha224-hash.sha224-hash                       
          This code uses a 224-bit hash function, which is deprecated or        
  disallowed in some security                                                   
          policies. Consider updating to a stronger hash function such as       
  SHA-384 or higher to ensure                                                   
          compliance and security.                                              
          Details: https://sg.run/Db1Yv                                         
                                                                                
           38┆ name = hashlib.sha224(key_bytes).hexdigest()
                                                                        
    venv/lib/python3.12/site-packages/pip/_internal/utils/subprocess.py 
       python.lang.compatibility.python36.python36-compatibility-Popen1  
          the `errors` argument to Popen is only available on Python 3.6+
          Details: https://sg.run/weBP                                   
                                                                         
          141┆ proc = subprocess.Popen(
          142┆     # Convert HiddenText objects to the underlying str.
          143┆     reveal_command_args(cmd),
          144┆     stdin=subprocess.PIPE,
          145┆     stdout=subprocess.PIPE,
          146┆     stderr=subprocess.STDOUT if not stdout_only else             
  subprocess.PIPE,                                                              
          147┆     cwd=cwd,
          148┆     env=env,
          149┆     errors="backslashreplace",
          150┆ )
                                                                       
    venv/lib/python3.12/site-packages/pip/_internal/utils/unpacking.py 
       python.lang.security.audit.insecure-file-permissions.insecure-file-permis
  sions                                                                         
          These permissions `$BITS` are widely permissive and grant access to   
  more people than may be                                                       
          necessary. A good default is `0o644` which gives read and write access
  to yourself and read                                                          
          access to everyone else.                                              
          Details: https://sg.run/AXY4                                          
                                                                                
           93┆ os.chmod(path, (0o777 & ~current_umask() | 0o111))
                                                                       
    venv/lib/python3.12/site-packages/pip/_vendor/cachecontrol/_cmd.py 
       python.lang.security.audit.insecure-transport.requests.request-session-wi
  th-http.request-session-with-                                                 
       http                                                                     
          Detected a request using 'http://'. This request will be unencrypted. 
  Use 'https://'                                                                
          instead.                                                              
          Details: https://sg.run/DoBY                                          
                                                                                
           33┆ sess.mount("http://", adapter)
                                                                                
    venv/lib/python3.12/site-packages/pip/_vendor/cachecontrol/caches/file_cache
  .py                                                                           
       python.lang.security.audit.sha224-hash.sha224-hash                       
          This code uses a 224-bit hash function, which is deprecated or        
  disallowed in some security                                                   
          policies. Consider updating to a stronger hash function such as       
  SHA-384 or higher to ensure                                                   
          compliance and security.                                              
          Details: https://sg.run/Db1Yv                                         
                                                                                
           95┆ return hashlib.sha224(x.encode()).hexdigest()
                                                                  
    venv/lib/python3.12/site-packages/pip/_vendor/certifi/core.py 
       python.lang.compatibility.python37.python37-compatibility-importlib2     
          Found 'importlib.resources', which is a module only available on      
  Python 3.7+. This does not                                                    
          work in lower versions, and therefore is not backwards compatible. Use
  importlib_resources                                                           
          instead for older Python versions.                                    
          Details: https://sg.run/eL3y                                          
                                                                                
           13┆ from importlib.resources import as_file, files
            ⋮┆----------------------------------------
           47┆ from importlib.resources import path as get_path, read_text
                                                                    
    venv/lib/python3.12/site-packages/pip/_vendor/distlib/compat.py 
       python.lang.security.use-defused-xmlrpc.use-defused-xmlrpc               
          Detected use of xmlrpc. xmlrpc is not inherently safe from            
  vulnerabilities. Use                                                          
          defusedxml.xmlrpc instead.                                            
          Details: https://sg.run/weqY                                          
                                                                                
           42┆ import xmlrpclib
            ⋮┆----------------------------------------
           81┆ import xmlrpc.client as xmlrpclib
                                                                  
    venv/lib/python3.12/site-packages/pip/_vendor/distlib/util.py 
       python.lang.security.audit.httpsconnection-detected.httpsconnection-detec
  ted                                                                           
          The HTTPSConnection API has changed frequently with minor releases of 
  Python. Ensure you are                                                        
          using the API for your version of Python securely. For example, Python
  3 versions prior to                                                           
          3.4.3 will not verify SSL certificates by default. See                
          https://docs.python.org/3/library/http.client.html#http.client.HTTPSCo
  nnection for more                                                             
          information.                                                          
          Details: https://sg.run/8yby                                          
                                                                                
         1601┆ self._connection = host, httplib.HTTPSConnection(
         1602┆     h, None, **kwargs)
                                                                            
    venv/lib/python3.12/site-packages/pip/_vendor/pkg_resources/__init__.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          151┆ state[k] = g['_sget_' + v](g[k])
            ⋮┆----------------------------------------
          151┆ state[k] = g['_sget_' + v](g[k])
            ⋮┆----------------------------------------
          158┆ g['_sset_' + _state_vars[k]](k, g[k], v)
            ⋮┆----------------------------------------
          158┆ g['_sset_' + _state_vars[k]](k, g[k], v)
            ⋮┆----------------------------------------
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
         1561┆ exec(code, namespace, namespace)
            ⋮┆----------------------------------------
         1572┆ exec(script_code, namespace, namespace)
            ⋮┆----------------------------------------
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
         2290┆ importlib.import_module(packageName)
                                                                                
    venv/lib/python3.12/site-packages/pip/_vendor/pygments/formatters/__init__.p
  y                                                                             
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          103┆ exec(f.read(), custom_namespace)
                                                                              
    venv/lib/python3.12/site-packages/pip/_vendor/pygments/lexers/__init__.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          153┆ exec(f.read(), custom_namespace)
                                                                        
    venv/lib/python3.12/site-packages/pip/_vendor/pygments/unistring.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
           83┆ return ''.join(globals()[cat] for cat in args)
            ⋮┆----------------------------------------
           90┆ return ''.join(globals()[cat] for cat in newcats)
                                                                                
    venv/lib/python3.12/site-packages/pip/_vendor/pyparsing/diagram/__init__.py 
       python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2
          Detected direct use of jinja2. If not done properly, this may bypass  
  HTML escaping which                                                           
          opens up the application to cross-site scripting (XSS)                
  vulnerabilities. Prefer using the                                             
          Flask method 'render_template()' and templates with a '.html'         
  extension in order to prevent                                                 
          XSS.                                                                  
          Details: https://sg.run/RoKe                                          
                                                                                
          157┆ return template.render(diagrams=data, embed=embed, **kwargs)
                                                                                
    venv/lib/python3.12/site-packages/pip/_vendor/pyproject_hooks/_in_process/__
  init__.py                                                                     
       python.lang.compatibility.python37.python37-compatibility-importlib2     
          Found 'importlib.resources', which is a module only available on      
  Python 3.7+. This does not                                                    
          work in lower versions, and therefore is not backwards compatible. Use
  importlib_resources                                                           
          instead for older Python versions.                                    
          Details: https://sg.run/eL3y                                          
                                                                                
            7┆ import importlib.resources as resources
                                                                                
    venv/lib/python3.12/site-packages/pip/_vendor/pyproject_hooks/_in_process/_i
  n_process.py                                                                  
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           77┆ obj = import_module(mod_path)
            ⋮┆----------------------------------------
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          329┆ hook = globals()[hook_name]
                                                                   
    venv/lib/python3.12/site-packages/pip/_vendor/requests/auth.py 
       python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha
  1                                                                             
          Detected SHA1 hash algorithm which is considered insecure. SHA1 is not
  collision resistant                                                           
          and is therefore not suitable as a cryptographic signature. Use SHA256
  or SHA3 instead.                                                              
          Details: https://sg.run/ydYx                                          
                                                                                
           ▶▶┆ Autofix ▶ hashlib.sha256(x)
          156┆ return hashlib.sha1(x).hexdigest()
            ⋮┆----------------------------------------
           ▶▶┆ Autofix ▶ hashlib.sha256(s)
          205┆ cnonce = hashlib.sha1(s).hexdigest()[:16]
                                                                
    venv/lib/python3.12/site-packages/pip/_vendor/rich/style.py 
       python.lang.security.audit.marshal.marshal-usage                         
          The marshal module is not intended to be secure against erroneous or  
  maliciously constructed                                                       
          data. Never unmarshal data received from an untrusted or              
  unauthenticated source. See more                                              
          details:                                                              
  https://docs.python.org/3/library/marshal.html?highlight=security             
          Details: https://sg.run/3xor                                          
                                                                                
          191┆ self._meta = None if meta is None else dumps(meta)
            ⋮┆----------------------------------------
          242┆ style._meta = dumps(meta)
            ⋮┆----------------------------------------
          475┆ return {} if self._meta is None else cast(Dict[str, Any],        
  loads(self._meta))                                                            
            ⋮┆----------------------------------------
          751┆ new_style._meta = dumps({**self.meta, **style.meta})
                                                                     
    venv/lib/python3.12/site-packages/pip/_vendor/truststore/_api.py 
       python.lang.security.audit.insecure-transport.ssl.no-set-ciphers.no-set-c
  iphers                                                                        
          The 'ssl' module disables insecure cipher suites by default.          
  Therefore, use of                                                             
          'set_ciphers()' should only be used when you have very specialized    
  requirements. Otherwise,                                                      
          you risk lowering the security of the SSL channel.                    
          Details: https://sg.run/0Q0v                                          
                                                                                
          160┆ return self._ctx.set_ciphers(__cipherlist)
                                                                               
    venv/lib/python3.12/site-packages/pip/_vendor/urllib3/contrib/pyopenssl.py 
       python.lang.security.audit.weak-ssl-version.weak-ssl-version             
          An insecure SSL version was detected. TLS versions 1.0, 1.1, and all  
  SSL versions are                                                              
          considered weak encryption and are deprecated. Use                    
  'ssl.PROTOCOL_TLSv1_2' or higher.                                             
          Details: https://sg.run/RoZO                                          
                                                                                
           99┆ ssl.PROTOCOL_TLSv1: OpenSSL.SSL.TLSv1_METHOD,
            ⋮┆----------------------------------------
          103┆ _openssl_versions[ssl.PROTOCOL_SSLv3] = OpenSSL.SSL.SSLv3_METHOD
            ⋮┆----------------------------------------
          106┆ _openssl_versions[ssl.PROTOCOL_TLSv1_1] =                        
  OpenSSL.SSL.TLSv1_1_METHOD                                                    
                                                                                
    venv/lib/python3.12/site-packages/pip/_vendor/urllib3/contrib/securetranspor
  t.py                                                                          
       python.lang.security.audit.weak-ssl-version.weak-ssl-version             
          An insecure SSL version was detected. TLS versions 1.0, 1.1, and all  
  SSL versions are                                                              
          considered weak encryption and are deprecated. Use                    
  'ssl.PROTOCOL_TLSv1_2' or higher.                                             
          Details: https://sg.run/RoZO                                          
                                                                                
          163┆ _protocol_to_min_max[ssl.PROTOCOL_SSLv2] = (
            ⋮┆----------------------------------------
          168┆ _protocol_to_min_max[ssl.PROTOCOL_SSLv3] = (
            ⋮┆----------------------------------------
          173┆ _protocol_to_min_max[ssl.PROTOCOL_TLSv1] = (
            ⋮┆----------------------------------------
          178┆ _protocol_to_min_max[ssl.PROTOCOL_TLSv1_1] = (
                                                                       
    venv/lib/python3.12/site-packages/pip/_vendor/urllib3/util/ssl_.py 
       python.lang.security.audit.ssl-wrap-socket-is-deprecated.ssl-wrap-socket-
  is-deprecated                                                                 
          'ssl.wrap_socket()' is deprecated. This function creates an insecure  
  socket without server                                                         
          name indication or hostname matching. Instead, create an SSL context  
  using                                                                         
          'ssl.SSLContext()' and use that to wrap a socket.                     
          Details: https://sg.run/PJOY                                          
                                                                                
          179┆ return wrap_socket(socket, ciphers=self.ciphers, **kwargs)
            ⋮┆----------------------------------------
       python.lang.security.audit.insecure-transport.ssl.no-set-ciphers.no-set-c
  iphers                                                                        
          The 'ssl' module disables insecure cipher suites by default.          
  Therefore, use of                                                             
          'set_ciphers()' should only be used when you have very specialized    
  requirements. Otherwise,                                                      
          you risk lowering the security of the SSL channel.                    
          Details: https://sg.run/0Q0v                                          
                                                                                
          292┆ context.set_ciphers(ciphers or DEFAULT_CIPHERS)
                                                                           
    venv/lib/python3.12/site-packages/pip/_vendor/webencodings/mklabels.py 
       python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use
  -detected                                                                     
          Detected a dynamic value being used with urllib. urllib supports      
  'file://' schemes, so a                                                       
          dynamic value controlled by a malicious actor may allow them to read  
  arbitrary files. Audit                                                        
          uses of urllib calls to ensure user data cannot control the URLs, or  
  consider using the                                                            
          'requests' library instead.                                           
          Details: https://sg.run/dKZZ                                          
                                                                                
           47┆ for category in json.loads(urlopen(url).read().decode('ascii'))
                                                       
    venv/lib/python3.12/site-packages/py/_code/code.py 
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
          103┆ return eval(code, self.f_globals, f_locals)
                                                        
    venv/lib/python3.12/site-packages/py/_path/svnwc.py 
       python.lang.security.audit.subprocess-shell-true.subprocess-shell-true   
          Found 'subprocess' function 'Popen' with 'shell=True'. This is        
  dangerous because this call                                                   
          will spawn the command using a shell process. Doing so propagates     
  current shell settings and                                                    
          variables, which makes it much easier for a malicious actor to execute
  commands. Use                                                                 
          'shell=False' instead.                                                
          Details: https://sg.run/J92w                                          
                                                                                
           ▶▶┆ Autofix ▶ False
          868┆ shell=True,
                                                             
    venv/lib/python3.12/site-packages/py/_process/cmdexec.py 
       python.lang.security.audit.subprocess-shell-true.subprocess-shell-true   
          Found 'subprocess' function 'Popen' with 'shell=True'. This is        
  dangerous because this call                                                   
          will spawn the command using a shell process. Doing so propagates     
  current shell settings and                                                    
          variables, which makes it much easier for a malicious actor to execute
  commands. Use                                                                 
          'shell=False' instead.                                                
          Details: https://sg.run/J92w                                          
                                                                                
           ▶▶┆ Autofix ▶ False
           15┆ process = subprocess.Popen(cmd, shell=True,
                                                                
    venv/lib/python3.12/site-packages/py/_process/forkedfunc.py 
       python.lang.security.audit.marshal.marshal-usage                         
          The marshal module is not intended to be secure against erroneous or  
  maliciously constructed                                                       
          data. Never unmarshal data received from an untrusted or              
  unauthenticated source. See more                                              
          details:                                                              
  https://docs.python.org/3/library/marshal.html?highlight=security             
          Details: https://sg.run/3xor                                          
                                                                                
           66┆ retvalf.write(marshal.dumps(retval))
            ⋮┆----------------------------------------
           97┆ retval = marshal.loads(retval_data)
                                                                      
    venv/lib/python3.12/site-packages/pygments/formatters/__init__.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          103┆ exec(f.read(), custom_namespace)
                                                                  
    venv/lib/python3.12/site-packages/pygments/lexers/__init__.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          154┆ exec(f.read(), custom_namespace)
                                                                       
    venv/lib/python3.12/site-packages/pygments/lexers/_lua_builtins.py 
       python.lang.security.audit.insecure-transport.urllib.insecure-urlopen.ins
  ecure-urlopen                                                                 
          Detected 'urllib.urlopen()' using 'http://'. This request will not be 
  encrypted. Use                                                                
          'https://' instead.                                                   
          Details: https://sg.run/oxB9                                          
                                                                                
           ▶▶┆ Autofix ▶ urlopen('https://www.lua.org/manual/')
          225┆ f = urlopen('http://www.lua.org/manual/')
            ⋮┆----------------------------------------
       python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use
  -detected                                                                     
          Detected a dynamic value being used with urllib. urllib supports      
  'file://' schemes, so a                                                       
          dynamic value controlled by a malicious actor may allow them to read  
  arbitrary files. Audit                                                        
          uses of urllib calls to ensure user data cannot control the URLs, or  
  consider using the                                                            
          'requests' library instead.                                           
          Details: https://sg.run/dKZZ                                          
                                                                                
          233┆ f = urlopen(f'http://www.lua.org/manual/{version}/')
                                                                       
    venv/lib/python3.12/site-packages/pygments/lexers/_php_builtins.py 
       trailofbits.python.tarfile-extractall-traversal.tarfile-extractall-traver
  sal                                                                           
          Possible path traversal through `tarfile.open($PATH).extractall()` if 
  the source tar is                                                             
          controlled by an attacker                                             
          Details: https://sg.run/2RLD                                          
                                                                                
         3300┆ with tarfile.open(download[0]) as tar:
         3301┆     if hasattr(tarfile.TarFile, 'extraction_filter'):
         3302┆         tar.extractall(filter='data')
         3303┆     else:
         3304┆         tar.extractall()
                                                            
    venv/lib/python3.12/site-packages/pygments/unistring.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
           83┆ return ''.join(globals()[cat] for cat in args)
            ⋮┆----------------------------------------
           90┆ return ''.join(globals()[cat] for cat in newcats)
                                                                             
    venv/lib/python3.12/site-packages/pylint/config/config_initialization.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
           58┆ exec(utils._unquote(config_data["init-hook"]))  # pylint:        
  disable=exec-used                                                             
                                                             
    venv/lib/python3.12/site-packages/pylint/config/utils.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          152┆ exec(value)  # pylint: disable=exec-used
                                                             
    venv/lib/python3.12/site-packages/pylint/lint/caching.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
           42┆ data = pickle.load(stream)
            ⋮┆----------------------------------------
           69┆ pickle.dump(results, stream)
                                                              
    venv/lib/python3.12/site-packages/pylint/lint/parallel.py 
       python.lang.security.deserialization.pickle.avoid-dill                   
          Avoid using `dill`, which uses `pickle`, which is known to lead to    
  code execution                                                                
          vulnerabilities. When unpickling, the serialized data could be        
  manipulated to run arbitrary                                                  
          code. Instead, consider serializing the relevant data as JSON or a    
  similar text-based                                                            
          serialization format.                                                 
          Details: https://sg.run/vzjA                                          
                                                                                
           47┆ _worker_linter = dill.loads(linter)
            ⋮┆----------------------------------------
          142┆ max_workers=jobs, initializer=initializer,                       
  initargs=(dill.dumps(linter),)                                                
                                                              
    venv/lib/python3.12/site-packages/pylint/lint/pylinter.py 
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
         1170┆ note = eval(evaluation, {}, stats_dict)  # pylint:               
  disable=eval-used                                                             
                                                                        
    venv/lib/python3.12/site-packages/pylint/reporters/json_reporter.py 
       python.lang.security.audit.eval-detected.eval-detected                   
          Detected the use of eval(). eval() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ZvrD                                          
                                                                                
          184┆ note: int = eval(  # pylint: disable=eval-used
          185┆     evaluation, {}, {**counts_dict, "statement": stats.statement 
  or 1}                                                                         
          186┆ )
                                                            
    venv/lib/python3.12/site-packages/pyparsing/__init__.py 
       python.lang.compatibility.python37.python37-compatibility-importlib2     
          Found 'importlib.resources', which is a module only available on      
  Python 3.7+. This does not                                                    
          work in lower versions, and therefore is not backwards compatible. Use
  importlib_resources                                                           
          instead for older Python versions.                                    
          Details: https://sg.run/eL3y                                          
                                                                                
          161┆ from importlib import resources
                                                                    
    venv/lib/python3.12/site-packages/pyparsing/diagram/__init__.py 
       python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2
          Detected direct use of jinja2. If not done properly, this may bypass  
  HTML escaping which                                                           
          opens up the application to cross-site scripting (XSS)                
  vulnerabilities. Prefer using the                                             
          Flask method 'render_template()' and templates with a '.html'         
  extension in order to prevent                                                 
          XSS.                                                                  
          Details: https://sg.run/RoKe                                          
                                                                                
          212┆ return template.render(diagrams=data, embed=embed, **kwargs)
                                                       
    venv/lib/python3.12/site-packages/pytz/__init__.py 
       python.lang.compatibility.python37.python37-compatibility-importlib2     
          Found 'importlib.resources', which is a module only available on      
  Python 3.7+. This does not                                                    
          work in lower versions, and therefore is not backwards compatible. Use
  importlib_resources                                                           
          instead for older Python versions.                                    
          Details: https://sg.run/eL3y                                          
                                                                                
          100┆ from importlib.resources import files
                                                        
    venv/lib/python3.12/site-packages/scipy/__init__.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          131┆ return _importlib.import_module(f'scipy.{name}')
            ⋮┆----------------------------------------
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          134┆ return globals()[name]
                                                                           
    venv/lib/python3.12/site-packages/scipy/_lib/_array_api_docs_tables.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          220┆ module = import_module(module_name)
                                                           
    venv/lib/python3.12/site-packages/scipy/_lib/_bunch.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          160┆ exec(s, namespace)
                                                                     
    venv/lib/python3.12/site-packages/scipy/_lib/_uarray/_backend.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           53┆ module = importlib.import_module(mod_name)
            ⋮┆----------------------------------------
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
           80┆ raise pickle.PicklingError(
           81┆     f"Can't pickle {func}: it's not the same object as {test}"
           82┆ )
                                                                               
    venv/lib/python3.12/site-packages/scipy/_lib/array_api_compat/_internal.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           60┆ mod = importlib.import_module(mod_name)
            ⋮┆----------------------------------------
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
           64┆ exec(f"from {mod.__name__} import *", objs)
                                                                              
    venv/lib/python3.12/site-packages/scipy/_lib/array_api_compat/cupy/fft.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
            7┆ exec("from cupy.fft import *", _n)
                                                                                
    venv/lib/python3.12/site-packages/scipy/_lib/array_api_compat/cupy/linalg.py
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
            6┆ exec('from cupy.linalg import *', _n)
                                                                
    venv/lib/python3.12/site-packages/scipy/_lib/deprecation.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           51┆ attr = getattr(import_module(correct_import), attribute, None)
            ⋮┆----------------------------------------
           72┆ return getattr(import_module(f"scipy.{sub_package}.{module}"),   
  attribute)                                                                    
                                                                  
    venv/lib/python3.12/site-packages/scipy/datasets/_fetchers.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
           83┆ ascent = array(pickle.load(f))
                                                                                
    venv/lib/python3.12/site-packages/scipy/ndimage/_support_alternative_backend
  s.py                                                                          
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           47┆ cupyx_module =                                                   
  importlib.import_module(f"cupyx.scipy.{module_name}")                         
                                                                
    venv/lib/python3.12/site-packages/scipy/optimize/_nonlin.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
         1635┆ exec(wrapper, ns)
                                                                     
    venv/lib/python3.12/site-packages/scipy/optimize/_root_scalar.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          242┆ v = locals().get(k)
                                                                                
    venv/lib/python3.12/site-packages/scipy/signal/_support_alternative_backends
  .py                                                                           
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           52┆ cupyx_module =                                                   
  importlib.import_module(f"cupyx.scipy.{module_name}")                         
                                                               
    venv/lib/python3.12/site-packages/scipy/sparse/__init__.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          342┆ return _importlib.import_module(f'scipy.sparse.{name}')
            ⋮┆----------------------------------------
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          345┆ return globals()[name]
                                                                                
    venv/lib/python3.12/site-packages/scipy/special/_support_alternative_backend
  s.py                                                                          
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          139┆ _f = globals()[self.name]  # Allow nested wrapping
            ⋮┆----------------------------------------
          156┆ _f = globals()[self.name]  # Allow nested wrapping
                                                                           
    venv/lib/python3.12/site-packages/scipy/stats/_distn_infrastructure.py 
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
          368┆ exec('del ' + obj)
            ⋮┆----------------------------------------
          747┆ exec(self._parse_arg_template, ns)
                                                          
    venv/lib/python3.12/site-packages/sklearn/__init__.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          131┆ return _importlib.import_module(f"sklearn.{name}")
            ⋮┆----------------------------------------
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          134┆ return globals()[name]
                                                                   
    venv/lib/python3.12/site-packages/sklearn/datasets/__init__.py 
       python.lang.security.dangerous-globals-use.dangerous-globals-use         
          Found non static data as an index to 'globals()'. This is extremely   
  dangerous because it                                                          
          allows an attacker to execute arbitrary code on the system. Refactor  
  your code not to use                                                          
          'globals()'.                                                          
          Details: https://sg.run/jNzn                                          
                                                                                
          166┆ return globals()[name]
                                                                
    venv/lib/python3.12/site-packages/sklearn/datasets/_base.py 
       python.lang.compatibility.python37.python37-compatibility-importlib2     
          Found 'importlib.resources', which is a module only available on      
  Python 3.7+. This does not                                                    
          work in lower versions, and therefore is not backwards compatible. Use
  importlib_resources                                                           
          instead for older Python versions.                                    
          Details: https://sg.run/eL3y                                          
                                                                                
           18┆ from importlib import resources
            ⋮┆----------------------------------------
       python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use
  -detected                                                                     
          Detected a dynamic value being used with urllib. urllib supports      
  'file://' schemes, so a                                                       
          dynamic value controlled by a malicious actor may allow them to read  
  arbitrary files. Audit                                                        
          uses of urllib calls to ensure user data cannot control the URLs, or  
  consider using the                                                            
          'requests' library instead.                                           
          Details: https://sg.run/dKZZ                                          
                                                                                
         1516┆ urlretrieve(remote.url, temp_file_path)
                                                                             
    venv/lib/python3.12/site-packages/sklearn/datasets/_twenty_newsgroups.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
           95┆ compressed_content = codecs.encode(pickle.dumps(cache),          
  "zlib_codec")                                                                 
            ⋮┆----------------------------------------
          310┆ cache = pickle.loads(uncompressed_content)
                                                                                
    venv/lib/python3.12/site-packages/sklearn/externals/array_api_compat/_intern
  al.py                                                                         
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           60┆ mod = importlib.import_module(mod_name)
            ⋮┆----------------------------------------
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
           64┆ exec(f"from {mod.__name__} import *", objs)
                                                                                
    venv/lib/python3.12/site-packages/sklearn/externals/array_api_compat/cupy/ff
  t.py                                                                          
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
            7┆ exec("from cupy.fft import *", _n)
                                                                                
    venv/lib/python3.12/site-packages/sklearn/externals/array_api_compat/cupy/li
  nalg.py                                                                       
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
            6┆ exec('from cupy.linalg import *', _n)
                                                                   
    venv/lib/python3.12/site-packages/sklearn/utils/_set_output.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
           18┆ return importlib.import_module(library)
                                                                
    venv/lib/python3.12/site-packages/sklearn/utils/_testing.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
         1328┆ array_mod = importlib.import_module(array_namespace)
                                                                 
    venv/lib/python3.12/site-packages/sklearn/utils/discovery.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
          102┆ module = import_module(module_name)
            ⋮┆----------------------------------------
          184┆ module = import_module(module_name)
            ⋮┆----------------------------------------
          243┆ module = import_module(module_name)
                                                                        
    venv/lib/python3.12/site-packages/sklearn/utils/estimator_checks.py 
       python.lang.security.deserialization.pickle.avoid-pickle                 
          Avoid using `pickle`, which is known to lead to code execution        
  vulnerabilities. When                                                         
          unpickling, the serialized data could be manipulated to run arbitrary 
  code. Instead,                                                                
          consider serializing the relevant data as JSON or a similar text-based
  serialization format.                                                         
          Details: https://sg.run/OPwB                                          
                                                                                
         2707┆ pickled_estimator = pickle.dumps(estimator)
            ⋮┆----------------------------------------
         2715┆ unpickled_estimator = pickle.loads(pickled_estimator)
            ⋮┆----------------------------------------
         3973┆ est = pickle.loads(pickle.dumps(est))
            ⋮┆----------------------------------------
         3973┆ est = pickle.loads(pickle.dumps(est))
                                                       
    venv/lib/python3.12/site-packages/threadpoolctl.py 
       python.lang.security.audit.non-literal-import.non-literal-import         
          Untrusted user input in `importlib.import_module()` function allows an
  attacker to load                                                              
          arbitrary code. Avoid dynamic values in `importlib.import_module()` or
  use a whitelist to                                                            
          prevent running untrusted code.                                       
          Details: https://sg.run/y6Jk                                          
                                                                                
         1281┆ importlib.import_module(module, package=None)
            ⋮┆----------------------------------------
       python.lang.security.audit.exec-detected.exec-detected                   
          Detected the use of exec(). exec() can be dangerous if used to        
  evaluate dynamic content. If                                                  
          this content can be input from outside the program, this may be a code
  injection                                                                     
          vulnerability. Ensure evaluated content is not definable by external  
  sources.                                                                      
          Details: https://sg.run/ndRX                                          
                                                                                
         1286┆ exec(options.command)
                
                
┌──────────────┐
│ Scan Summary │
└──────────────┘
Some files were skipped or only partially analyzed.
  Partially scanned: 47 files only partially analyzed due to parsing or internal Semgrep errors
  Scan skipped: 22 files larger than 1.0 MB, 3404 files matching .semgrepignore patterns
  For a full list of skipped files, run semgrep with the --verbose flag.

Ran 501 rules on 9378 files: 241 findings.

A new version of Semgrep is available. See https://semgrep.dev/docs/upgrading

Versions prior to 1.76.0 are no longer supported by Semgrep.dev, please upgrade.

