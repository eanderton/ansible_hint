Work in Progress
================

ansible_hint is a work-in-progress and is not yet ready for public consumption.

ansible_hint
============

A work-in-progress tool for checking Ansible code using a configurable set of rules.


Roadmap
=======

Motivation
----------

The motivation for this project stems from a host of problems in this space.  Typically, 
the "right" answer to any software problem is to integrate existing parts, or contribute 
back to existing projects.  Since the requirements for ansible_hint position are not 
well-served by existing YAML and Ansible-lint implementations, a scratch-built project
is the only way forward.

* Full warning/error output with line and column information
* Preservation of whitespace for indentation checks and other formatting issues
* Support for custom rules and validations
* Pasring of comments for sphinx-like metadata support, suitable for doc generation

The existing YAML libraries surveyed support the above to some extent, but do not provide a
clean integration path to this solution. PyYAML is a great YAML implementtaion, it lacks
position, whitespace, and comment metadata.  Ruamel.yaml does provide this information, 
but isn't 100% consistent with position information, as it is not provided for every 
token in the parser output.  Also, both libraries throw away leading and internal
whitespace, requiring the developer to build a crude parser on top of the library to 
tease this information out of the original file.

As for needing a better Ansible linter, the existing linters out there are limited by 
PyYAML's lack of metadata, or simply target vanilla YAML without concern for Ansible's
extensions within that grammar.  There is a clear need for a linter that understands
Ansible and YAML both, right down to every character in the file.


Phase I - BNF Parser Generator
------------------------------

This project will use a custom parser based on SimpleParse, as a pure-python implementation
to avoid any bugs, install-time quirks, and increase maintainability. Based on @eanderton's 
previous work on Enki, the first cut of the parser will be a simple recursive descent
implementation with a focus on ease-of-maintenance over performance

Future versions of this component may by spun out to its own project as something to be 
optimized over time.  Additionally, like Enki, the component may become a pre-processor 
used to generate Python code directly, instead of composing the parser from BNF at runtime.

The goal is to have a parser that can generate additional parsers by specifying the grammar
using SimpleParse's BNF variant.

Features:

* UTF-8 support
* Support for SimpleParse BNF
* On-the-fly parser generation
* AST node output with full line/col position information

Phase II - YAML Parser
---------------------

The YAML parser used by ansible_hint will use the parser generator to compose a YAML parser
that is specified using BNF.  There is at least one such grammar online, but it will require
a custom-built AST walk along with robust validations.

Like the Phase I parser, this component should be suitable for an eventual project spin-off.

The goal is to have a fully-compliant YAML 1.2 parser.

Features:

* YAML 1.2 compliant implementation
* Full YAML validation suite (either sourced from 3rd party or custom)
* Metadata support for every YAML element
** Position information
** leading whitespace
** trailing whitespace
** associated comment text

Phase III - Ansible Linter
--------------------------

The final phase of the project will be the final linter implementation.  Building on the
parser from Phase II, the linter will fulfill the project requirements.

* Full warning/error output with line and column information
* Preservation of whitespace for indentation checks and other formatting issues
* Support for custom rules and validations
* Pasring of comments for sphinx-like metadata support, suitable for doc generation
