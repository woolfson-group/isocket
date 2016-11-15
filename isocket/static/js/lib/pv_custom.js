function loadpdb(pdb) {
  // asynchronously load the PDB file for the dengue methyl transferase
  // from the server and display it in the viewer.
  pv.io.fetchPdb(pdb, function(structure) {
      // display the protein as cartoon, coloring the secondary structure
      // elements in a rainbow gradient.
      viewer.cartoon('protein', structure, { color : color.ssSuccession() });
      // there are two ligands in the structure, the co-factor S-adenosyl
      // homocysteine and the inhibitor ribavirin-5' triphosphate. They have
      // the three-letter codes SAH and RVP, respectively. Let's display them
      // with balls and sticks.
      viewer.centerOn(structure);
  });
}