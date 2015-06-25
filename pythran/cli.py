#!/usr/bin/env python

""" Script to run Pythran file compilation with specified g++ like flags. """

import sys
import os
import argparse
import logging
import pythran

from distutils.errors import CompileError

logger = logging.getLogger("pythran")

# Initialize logging
try:
    # Set a nice colored output
    from colorlog import ColoredFormatter
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red',
        }
    )
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
except ImportError:
    # No color available, use default config
    logging.basicConfig(format='%(levelname)s: %(message)s')
    logger.warn("Disabling color, you really want to install colorlog.")


def convert_arg_line_to_args(arg_line):
    """Read argument from file in a prettier way."""
    for arg in arg_line.split():
        if not arg.strip():
            continue
        yield arg


def compile_flags(args):
    """
    Build a dictionnary with an entry for cppflags, ldflags, and cxxflags.

    These options are filled according to the command line defined options

    """

    compiler_options = {
        'define_macros': args.defines,
        'include_dirs': args.include_dirs,
        'extra_compile_args': args.extra_flags,
        'library_dirs': args.libraries_dir,
        'extra_link_args': args.extra_flags,
    }
    if args.opts:
        compiler_options['opts'] = args.opts

    return compiler_options

def run():
    parser = argparse.ArgumentParser(prog='pythran',
                                     description='pythran: a python to C++ '
                                     'compiler',
                                     epilog="It's a megablast!",
                                     fromfile_prefix_chars="@")

    parser.add_argument('input_file', type=str,
                        help='the pythran module to compile, either a .py or a '
                        '.cpp file')

    parser.add_argument('-o', dest='output_file', type=str,
                        help='path to generated file')

    parser.add_argument('-E', dest='translate_only', action='store_true',
                        help='only run the translator, do not compile')

    parser.add_argument('-e', dest='raw_translate_only', action='store_true',
                        help='similar to -E, but does not generate python glue')

    parser.add_argument('-v', dest='verbose', action='store_true',
                        help='be verbose')

    parser.add_argument('-p', dest='opts', metavar='pass',
                        action='append',
                        help='any pythran optimization to apply before code '
                        'generation',
                        default=list())

    parser.add_argument('-I', dest='include_dirs', metavar='include_dir',
                        action='append',
                        help='any include dir relevant to the underlying C++ '
                        'compiler',
                        default=list())

    parser.add_argument('-L', dest='libraries_dir', metavar='ldflags',
                        action='append',
                        help='any search dir relevant to the linker',
                        default=list())

    parser.add_argument('-D', dest='defines', metavar='macro_definition',
                        action='append',
                        help='any macro definition relevant to the underlying C++ '
                        'compiler',
                        default=list())

    parser.convert_arg_line_to_args = convert_arg_line_to_args

    args, extra = parser.parse_known_args(sys.argv[1:])
    args.extra_flags = extra
    if args.raw_translate_only:
        args.translate_only = True

    if args.verbose:
        logger.setLevel(logging.INFO)

    try:
        if not os.path.exists(args.input_file):
            raise ValueError("input file `{0}' not found".format(args.input_file))

        module_name, ext = os.path.splitext(os.path.basename(args.input_file))

        if ext not in ['.cpp', '.py']:  # FIXME: do we support other ext than .cpp?
            raise SyntaxError("Unsupported file extension: '{0}'".format(ext))

        if ext == '.cpp':
            if args.translate_only:
                raise ValueError("Do you really ask for Python-to-C++ on this C++ "
                                 "input file: '{0}'?".format(args.input_file))
            pythran.compile_cxxfile(module_name,
                                    args.input_file, args.output_file,
                                    **compile_flags(args))

        else:  # assume we have a .py input file here

            pythran.compile_pythranfile(args.input_file,
                                        output_file=args.output_file,
                                        cpponly=args.translate_only,
                                        **compile_flags(args))


    except IOError as e:
        logger.critical("I've got a bad feeling about this...\n"
                        "E: " + str(e))
        sys.exit(1)
    except ValueError as e:
        logger.critical("Chair to keyboard interface error\n"
                        "E: " + str(e))
        sys.exit(1)
    except SyntaxError as e:
        logger.critical("I am in trouble. Your input file does not seem "
                        "to match Pythran's constraints...\n"
                        "E: " + str(e))
        sys.exit(1)
    except CompileError as e:
        logger.critical("Cover me Jack. Jack? Jaaaaack!!!!\n"
                        "E: " + str(e))
        sys.exit(1)
    except NotImplementedError as e:
        logger.critical("MAYDAY, MAYDAY, MAYDAY; pythran compiler; "
                        "code area out of control\n"
                        "E: not implemented feature needed, "
                        "bash the developers")
        raise  # Why ? we may instead display the stacktrace and exit?
    except EnvironmentError as e:
        logger.critical("By Jove! Your environment does not seem "
                        "to provide all what we need\n"
                        "E: " + str(e))
        sys.exit(1)