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
//virtual sut_type
//virtual sut_name
//virtual sut_version

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
sut_type << virtual.sut_type;
sut_name << virtual.sut_name;
sut_version << virtual.sut_version;
@@

// firehose call
coccilib.xml_firehose.import_firehose()
coccilib.xml_firehose.print_issue(location=p0,
                                  message="semicolon after if",
                                  sut_type=sut_type,
                                  sut_name=sut_name,
                                  sut_version=sut_version)
