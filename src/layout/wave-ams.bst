%% AMS-style bibliography for Wave Motions in the Ocean.
%% The current bibliography contains @article and @book entries only.
%% Formatting follows the American Meteorological Society reference guide:
%% author(s), year: title. Publication data.

ENTRY
  { author editor title year journal shortjournal volume pages publisher edition }
  {}
  { label sort.label }

INTEGERS { nameptr namesleft numnames }
STRINGS { s t u }

FUNCTION {output.bibitem}
{
  newline$
  "\bibitem[" write$
  label write$
  "]{" write$
  cite$ write$
  "}" write$
  newline$
}

FUNCTION {format.names}
{
  's :=
  #1 'nameptr :=
  s num.names$ 'numnames :=
  numnames 'namesleft :=
  "" 't :=
  { namesleft #0 > }
  {
    s nameptr
    nameptr #1 =
      { "{vv~}{ll}{, f.}" }
      { "{f.~}{vv~}{ll}" }
    if$
    format.name$ 'u :=
    nameptr #1 >
      {
        namesleft #1 >
          { t ", " * u * 't := }
          {
            numnames #2 >
              { t ", and " * u * 't := }
              { t ", and " * u * 't := }
            if$
          }
        if$
      }
      { u 't := }
    if$
    nameptr #1 + 'nameptr :=
    namesleft #1 - 'namesleft :=
  }
  while$
  t
}

FUNCTION {format.contributors}
{
  author empty$
    {
      editor empty$
        { "" }
        {
          editor format.names
          editor num.names$ #1 >
            { ", Eds." * }
            { ", Ed." * }
          if$
        }
      if$
    }
    { author format.names }
  if$
}

FUNCTION {format.label.names}
{
  's :=
  s #1 "{vv~}{ll}" format.name$
  s num.names$ #1 =
    'skip$
    {
      s num.names$ #2 =
        { " and " * s #2 "{vv~}{ll}" format.name$ * }
        { " et~al." * }
      if$
    }
  if$
}

FUNCTION {calc.label}
{
  author empty$
    { editor format.label.names }
    { author format.label.names }
  if$
  "(" * year * ")" * 'label :=
}

FUNCTION {ordinal.edition}
{
  edition "1" =
    { "1st ed." }
    { edition "2" =
        { "2nd ed." }
        { edition "3" =
            { "3rd ed." }
            { edition "4" =
                { "4th ed." }
                { edition "5" =
                    { "5th ed." }
                    { edition "6" =
                        { "6th ed." }
                        { edition " " * "ed." * }
                      if$
                    }
                  if$
                }
              if$
            }
          if$
        }
      if$
    }
  if$
}

FUNCTION {format.journal}
{
  shortjournal empty$
    { journal }
    { shortjournal }
  if$
}

FUNCTION {article}
{
  output.bibitem
  format.contributors write$
  ", " write$
  year write$
  ": " write$
  title write$
  ". " write$
  "\textit{" write$ format.journal write$ "}" write$
  volume empty$
    'skip$
    { ", \textbf{" write$ volume write$ "}" write$ }
  if$
  pages empty$
    'skip$
    { ", " write$ pages write$ }
  if$
  "." write$
  newline$
}

FUNCTION {book}
{
  output.bibitem
  format.contributors write$
  ", " write$
  year write$
  ": " write$
  "\textit{" write$ title write$ "}. " write$
  edition empty$
    'skip$
    { ordinal.edition write$ ", " write$ }
  if$
  publisher write$
  pages empty$
    'skip$
    { ", " write$ pages write$ " pp" write$ }
  if$
  "." write$
  newline$
}

FUNCTION {misc}
{
  output.bibitem
  format.contributors write$
  ", " write$
  year write$
  ": " write$
  title write$
  "." write$
  newline$
}

FUNCTION {default.type} { misc }

FUNCTION {field.or.null}
{ duplicate$ empty$ { pop$ "" } 'skip$ if$ }

FUNCTION {sortify}
{ purify$ "l" change.case$ }

FUNCTION {presort}
{
  author empty$
    { editor field.or.null }
    { author }
  if$
  sortify
  "    " * year field.or.null sortify *
  "    " * title field.or.null sortify *
  'sort.label :=
  sort.label 'sort.key$ :=
}

FUNCTION {begin.bib}
{
  "\begin{thebibliography}{99}" write$ newline$
  "\providecommand{\natexlab}[1]{#1}" write$ newline$
}

FUNCTION {end.bib}
{ newline$ "\end{thebibliography}" write$ newline$ }

READ
ITERATE {calc.label}
ITERATE {presort}
SORT
EXECUTE {begin.bib}
ITERATE {call.type$}
EXECUTE {end.bib}
