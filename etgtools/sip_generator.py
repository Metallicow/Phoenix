#---------------------------------------------------------------------------
# Name:        etgtools/sip_generator.py
# Author:      Robin Dunn
#
# Created:     3-Nov-2010
# Copyright:   (c) 2010 by Total Control Software
# Licence:     wxWindows license
#---------------------------------------------------------------------------

"""
The generator class for creating SIP definition files from the data
objects produced by the ETG scripts.
"""

import sys, os
import extractors
import generators
from cStringIO import StringIO


divider = '//' + '-'*75 + '\n'
phoenixRoot = os.path.abspath(os.path.split(__file__)[0]+'/..')

#---------------------------------------------------------------------------

class SipWrapperGenerator(generators.WrapperGeneratorBase):
        
    def generate(self, module, destFile=None):
        stream = StringIO()
        
        # generate SIP code from the module and its objects
        self.generateModule(module, stream)
        
        # Write the contents of the stream to the destination file
        if not destFile:
            destFile = os.path.join(phoenixRoot, 'sip/gen', module.name + '.sip')
        file(destFile, 'wt').write(stream.getvalue())
            
        
    #-----------------------------------------------------------------------
    def generateModule(self, module, stream):
        assert isinstance(module, extractors.ModuleDef)

        # write the file header
        stream.write(divider + """\
// This file is generated by wxPython's SIP generator.  Do not edit by hand.
// 
// Copyright: (c) 2010 by Total Control Software
// Licence:   wxWindows license
""")
        if module.name == module.module:
            stream.write("""
%%Module %s.%s
%%Copying
    Copyright: (c) 2010 by Total Control Software
    Licence:   wxWindows license
%%End
%%RealArgNames

""" % (module.package, module.name))
            
        else:
            stream.write("//\n// This file is included from %s.sip\n//\n" % module.module)
        
        stream.write(divider)
            
        # %Imports and %Includes
        for i in module.imports:
            stream.write("%%Import %s.sip\n" % i)
        stream.write("\n")
        for i in module.includes:
            stream.write("%%Include %s.sip\n" % i)

        # C++ code to be written out to the generated module
        if module.headerCode:
            stream.write("\n%ModuleHeaderCode\n")
            for c in module.headerCode:
                stream.write('%s\n' % c)
            stream.write("%End\n\n")
        
        if module.cppCode:
            stream.write("%ModuleCode\n")
            for c in module.cppCode:
                stream.write('%s\n' % c)
            stream.write("%End\n")

        stream.write('\n%s\n' % divider)
            
        # Now generate each of the items in the module
        self.generateModuleItems(module, stream)
                    
        # Add code for the module initialization sections.
        if module.preInitializerCode:
            stream.write('\n%s\n\n%%PreInitialisationCode\n' % divider)
            for i in module.preInitializerCode:
                stream.write('%s\n' % i)
            stream.write('%End\n')            
        if module.initializerCode:
            stream.write('\n%s\n\n%%InitialisationCode\n' % divider)
            for i in module.initializerCode:
                stream.write('%s\n' % i)
            stream.write('%End\n')            
        if module.postInitializerCode:
            stream.write('\n%s\n\n%%PostInitialisationCode\n' % divider)
            for i in module.postInitializerCode:
                stream.write('%s\n' % i)
            stream.write('%End\n')            
            
        stream.write('\n%s\n' % divider)
        
        
        
    def generateModuleItems(self, module, stream):
        methodMap = {
            extractors.ClassDef     : self.generateClass,
            extractors.FunctionDef  : self.generateFunction,
            extractors.EnumDef      : self.generateEnum,
            extractors.GlobalVarDef : self.generateGlobalVar,
            extractors.TypedefDef   : self.generateTypedef,
            extractors.WigCode      : self.generateWigCode,
            }
        
        for item in module:
            if item.ignored:
                continue
            function = methodMap[item.__class__]
            function(item, stream)
        
        
    #-----------------------------------------------------------------------
    def generateFunction(self, function, stream):
        assert isinstance(function, extractors.FunctionDef)
        if not function.ignored:
            stream.write('%s %s(' % (function.type, function.name))
            if function.items:
                stream.write('\n')
                self.generateParameters(function.items, stream, ' '*4)
            stream.write(')%s;\n' % self.annotate(function))
        for f in function.overloads:
            self.generateFunction(f, stream)
        stream.write('\n')            

        
    def generateParameters(self, parameters, stream, indent):
        for idx, param in enumerate(parameters):
            if param.ignored:
                continue
            stream.write(indent)
            stream.write('%s %s' % (param.type, param.name))
            if param.default:
                stream.write(' = %s' % param.default)
            stream.write(self.annotate(param))
            if not idx == len(parameters)-1:
                stream.write(',')
            stream.write('\n')
        
        
    #-----------------------------------------------------------------------
    def generateEnum(self, enum, stream, indent=''):
        assert isinstance(enum, extractors.EnumDef)
        if enum.ignored:
            return
        name = enum.name
        if name.startswith('@'):
            name = ''
        stream.write('%senum %s%s\n{\n' % (indent, name, self.annotate(enum)))
        values = []
        for v in enum.items:
            if v.ignored:
                continue
            values.append("%s    %s%s" % (indent, v.name, self.annotate(v)))
        stream.write(',\n'.join(values))
        stream.write('%s\n};\n\n' % (indent, ))
        
        
    #-----------------------------------------------------------------------
    def generateGlobalVar(self, globalVar, stream):
        assert isinstance(globalVar, extractors.GlobalVarDef)
        if globalVar.ignored:
            return
        stream.write('%s %s' % (globalVar.type, globalVar.name))
        stream.write('%s;\n\n' % self.annotate(globalVar))
        
        
    #-----------------------------------------------------------------------
    def generateTypedef(self, typedef, stream):
        assert isinstance(typedef, extractors.TypedefDef)
        if typedef.ignored:
            return
        stream.write('typedef %s %s' % (typedef.type, typedef.name))
        stream.write('%s;\n\n' % self.annotate(typedef))
        
        
    #-----------------------------------------------------------------------
    def generateWigCode(self, wig, stream, indent=''):
        assert isinstance(wig, extractors.WigCode)
        lines = [indent+line for line in wig.code.split('\n')]
        stream.write('\n'.join(lines))
        stream.write('\n\n')
    
    
    #-----------------------------------------------------------------------
    def generateClass(self, klass, stream, indent=''):
        assert isinstance(klass, extractors.ClassDef)
        if klass.ignored:
            return
        
        # write the class header
        stream.write('%sclass %s' % (indent, klass.name))
        if klass.bases:
            stream.write(' : ')
            stream.write(', '.join(klass.bases))
        stream.write(self.annotate(klass))
        stream.write('\n%s{\n' % indent)
        if klass.includes:
            stream.write('%s%%TypeHeaderCode\n' % indent)
            for inc in klass.includes:
                stream.write('%s    #include <%s>\n' % (indent, inc))
            stream.write('%s%%End\n' % indent)
        stream.write('\n%spublic:\n' % indent)
        
        # Split the items into public and protected groups
        ctors = [i for i in klass if 
                    isinstance(i, extractors.MethodDef) and 
                    i.protection == 'public' and (i.isCtor or i.isDtor)]
        public = [i for i in klass if i.protection == 'public' and i not in ctors]
        protected = [i for i in klass if i.protection == 'protected']
        
        dispatch = {
            extractors.MemberVarDef    : self.generateMemberVar,
            extractors.PropertyDef     : self.generateProperty,
            extractors.MethodDef       : self.generateMethod,
            extractors.EnumDef         : self.generateEnum,
            extractors.CppMethodDef    : self.generateCppMethod,
            extractors.WigCode         : self.generateWigCode,
            # TODO: nested classes too?
            }
        for item in ctors:
            f = dispatch[item.__class__]
            f(item, stream, indent + ' '*4)
            
        for item in public:
            f = dispatch[item.__class__]
            f(item, stream, indent + ' '*4)

        if protected and [i for i in protected if not i.ignored]:
            stream.write('\nprotected:\n')
            for item in protected:
                f = dispatch[item.__class__]
                f(item, stream, indent + ' '*4)

        if klass.convertFromPyObject:
            stream.write('%s%%ConvertToTypeCode\n' % indent)
            lines = [indent+l for l in klass.convertFromPyObject.split('\n')]
            stream.write('\n'.join(lines))
            stream.write('%s%%End\n' % indent)

        if klass.convertToPyObject:
            stream.write('%s%%ConvertFromTypeCode\n' % indent)
            lines = [indent+l for l in klass.convertToPyObject.split('\n')]
            stream.write('\n'.join(lines))
            stream.write('%s%%End\n' % indent)
            
        stream.write('%s};  // end of class %s\n\n\n' % (indent, klass.name))
        
        
            

    def generateMemberVar(self, memberVar, stream, indent):
        assert isinstance(memberVar, extractors.MemberVarDef)
        if memberVar.ignored:
            return
        stream.write('%s%s %s' % (indent, memberVar.type, memberVar.name))
        stream.write('%s;\n' % self.annotate(memberVar))

        
    def generateProperty(self, prop, stream, indent):
        assert isinstance(prop, extractors.PropertyDef)
        if prop.ignored:
            return
        stream.write('%s%%Property(name=%s, get=%s' % (indent, prop.name, prop.getter))
        if prop.setter:
            stream.write(', set=%s' % prop.setter)
        stream.write(')')
        if prop.briefDoc:
            stream.write(' // %s' % prop.briefDoc)
        stream.write('\n')
        
        
    def generateMethod(self, method, stream, indent):
        assert isinstance(method, extractors.MethodDef)
        if not method.ignored:
            if method.isVirtual:
                stream.write("%svirtual\n" % indent)
            if method.isStatic:
                stream.write("%sstatic\n" % indent)
            if method.isCtor or method.isDtor:
                stream.write('%s%s(' % (indent, method.name))
            else:
                stream.write('%s%s %s(' % (indent, method.type, method.name))
            if method.items:
                stream.write('\n')
                self.generateParameters(method.items, stream, indent+' '*4)
                stream.write(indent)
            stream.write(')%s;\n\n' % self.annotate(method))
        if method.overloads:
            for m in method.overloads:
                self.generateMethod(m, stream, indent)

            
    def generateCppMethod(self, method, stream, indent):
        assert isinstance(method, extractors.CppMethodDef)
        if method.ignored:
            return
        if method.isCtor:
            stream.write('%s%s%s%s;\n' % 
                         (indent, method.name, method.argsString, self.annotate(method)))
        else:
            stream.write('%s%s %s%s%s;\n' % 
                         (indent, method.type, method.name, method.argsString, 
                          self.annotate(method)))
        stream.write('%s%%MethodCode\n' % indent)
        lines = [indent+l for l in method.body.split('\n')]
        stream.write('\n'.join(lines))
        if len(lines) == 1:
            stream.write('\n%s' % indent)
        stream.write('%End\n\n')
        
    #-----------------------------------------------------------------------

    def annotate(self, item):
        annotations = []
        if item.pyName:
            annotations.append('PyName=%s' % item.pyName)

        if isinstance(item, extractors.ParamDef):
            if item.out:
                annotations.append('Out')
            if item.inOut:
                annotations.extend(['In', 'Out'])
            if item.array:
                annotations.append('Array')
            if item.arraySize:
                annotations.append('ArraySize')
                
        if isinstance(item, (extractors.ParamDef, extractors.FunctionDef)):
            if item.transfer:
                annotations.append('Transfer')
            if item.transferBack:
                annotations.append('TransferBack')
            if item.transferThis:
                annotations.append('TranserThis')

        if isinstance(item, extractors.FunctionDef):
            if item.deprecated:
                annotations.append('Deprecated')
            if item.factory:
                annotations.append('Factory')
            if item.pyReleaseGIL:   # else HoldGIL??
                annotations.append('ReleaseGIL')
            if item.noCopy:
                annotations.append('NoCopy')
            
        if isinstance(item, extractors.MethodDef):
            if item.defaultCtor:
                annotations.append('Default')
            
        if isinstance(item, extractors.ClassDef):
            if item.abstract:
                annotations.append('Abstract')
            if item.deprecated:
                annotations.append('Deprecated')
            if item.external:
                annotations.append('External')
            if item.noDefCtor:
                annotations.append('NoDefaultCtors')
            if item.singlton:
                annotations.append('DelayDtor')
        
        if annotations:
            return '   /%s/' % ', '.join(annotations)
        else:
            return ''

#---------------------------------------------------------------------------
