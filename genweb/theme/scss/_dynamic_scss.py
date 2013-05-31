
dynamic_scss = """
// Albert, aqui va la part d'scss dinamic amb els colors especifics

$genwebPrimary: %(especific1)s;
$genwebTitles: %(especific2)s;

//ANIMATION res de res

//BASE
#portal-header {border-top:5px solid desaturate(lighten($genwebPrimary,40%), 85%);}
#portal-header .container {border-top:5px solid $genwebPrimary;}
.l2-image:before {background:$genwebPrimary;}
#bandaLogos {border-top:1px solid desaturate(lighten($genwebPrimary,40%), 85%);}
#bandaLogos .container {border-top:1px solid darken($genwebPrimary,25%); }
#peu {border-top:5px solid desaturate(lighten($genwebPrimary,40%), 85%);}
#peu .container {border-top:5px solid $genwebPrimary; }
.sobreElWeb li:before {	color: desaturate($genwebPrimary, 80%);	}

//EDIT res de res

//EMPAQUETATS
.portaltype-packet .estudis .note { border: 5px solid lighten($genwebPrimary, 25%);}
GW3toGW4
//
.destacatBandejat {border-top:5px solid $genwebPrimary;}
.destacatQuadres {border: 5px solid lighten($genwebPrimary, 25%);}
div.fitxa {border-right:20px solid lighten($genwebPrimary,35%);}

//IE res de res
//INPUTS res de res

//LEAD 
.lead-small { border: 5px solid lighten($genwebPrimary, 25%);}
.lead-large { border-top:5px solid $genwebPrimary;}

//LISTS
.list li:before, .list-index li:before, .list-striped li:before, .list-hover li:before, .list-bordered li:before, .list-notebook li:before, .list-condensed li:before, .list-links li:before, .list-highlighted li:before, .list-portlet li:before { color: lighten($genwebPrimary, 15%);}
.list-index li:before {color: $genwebTitles;}

//MOBILE res de res
//NAV res de res
//PLANTILLES res de res

//PLONE
label { color: $genwebTitles;}
div.label, label *.label { color: $genwebTitles;}

//PORTLETS
.portlet h2 { border-bottom: 5px solid $genwebPrimary; }
.portlet-inverse h2 { background: $genwebPrimary;}

//PRINT res de res
//RETINA res de res
//SIMULATED VIEWS res de res

//TABLES
.table tr:first-child td {border-top:5px solid lighten($genwebPrimary, 10%);}

//TEXTS
h1, h2, h3 {color:$genwebTitles; }

//UI res de res
//UPCNET res de res

//WELL-BOXES
.sheet { border-right:20px solid lighten($genwebPrimary,35%); }




// ...
"""
