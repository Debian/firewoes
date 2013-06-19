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


@initialize:python depends on firehose@
coccilib.xml_firehose.import_firehose()
analysis = coccilib.xml_firehose.Analysis(use_env_variables=True)

@finalize:python depends on firehose@
analysis.print_analysis()

@script:python depends on firehose@
p0 << r1.p;
@@
analysis.add_result(p0, "semicolon after if")
