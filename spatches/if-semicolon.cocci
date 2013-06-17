//
//  Detect semicolon after if
//
// Target: Linux, Generic
// Copyright:  2012 - LIP6/INRIA
// License:  Licensed under ISC. See LICENSE or http://www.isc.org/software/license
// Author: Peter Senna Tschudin <peter.senna@gmail.com>
// URL: http://coccinelle.lip6.fr/ 
// URL: http://coccinellery.org/ 

virtual firehose

@r1@
position p;
@@
if (...);@p

@script:python depends on !firehose@
p0 << r1.p;
@@

// Emacs org-mode output
cocci.print_main("", p0)
cocci.print_secs("", p0)

@script:python depends on firehose@
p0 << r1.p;
@@

// firehose call
coccilib.xml_firehose.import_firehose()
coccilib.xml_firehose.print_issue(p0, "semicolon after if")
