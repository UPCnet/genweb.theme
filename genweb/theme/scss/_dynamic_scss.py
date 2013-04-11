
dynamic_scss = """
// Albert, aqui va la part d'scss dinamic amb els colors especifics

$genwebPrimary: %(especific1)s;
$genwebTitles: %(especific2)s;


//BASE
#portal-header {border-top:5px solid desaturate(lighten($genwebPrimary,40%), 85%);}
#portal-header .container {border-top:5px solid $genwebPrimary;}

// ...
"""
