
if exists("b:current_syntax")
  finish
endif

syntax keyword   directive    object type enum root
syntax keyword   modifier     optional nullable extends
syntax match     specifier    "\v\w+\s*(\=)@="
syntax match     label        "\v\w+\s*(:)@="
syntax match     type         "\v\w+\s*(\{|extends)@="
syntax region    text         start=+\z(["'`]\)+ skip=+\\\z1+ end=+\z1+ contains=@Spell
syntax match     number       "[-+]\=\<\d\+\(\.\d*\)\=\>"
syntax keyword   boolean      false true
syntax match     brackets     "[()\[\]]"
syntax match     comment      "^\#.*$"

hi def link directive    Title
hi def link modifier     PreProc
hi def link specifier    Structure
hi def link label        Identifier
hi def link type         Type
hi def link text         String
hi def link number       Number
hi def link boolean      Special
hi def link brackets     Special
hi def link comment      Comment

let b:current_syntax = "jsonbp"

