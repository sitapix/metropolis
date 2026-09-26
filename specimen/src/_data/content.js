// The words on the specimen. Each block is used by one section of the page, in
// page order. Delete a sample to drop its chip from the playground.

module.exports = {
	// Hero. The big word responds to the pointer, so keep it short.
	hero: "Metropolis",
	tagline:
		"A variable version of Chris Simpson’s geometric sans, in roman and italic.",

	// Playground. The first sample loads with the page; the rest are chips.
	samples: [
		{
			label: "Street",
			text:
				"Harbour Street, 7:42 on a Tuesday. The first tram rattles past the fish market while Jo buys a dozen quince tarts and a box of figs from a van outside. The bakery on the corner is already out of rye, and a man in a yellow jacket sweeps the steps of the old post office."
		},
		{ label: "Headline", text: "Night trains to the city of glass" },
		{
			label: "Numbers",
			text: "$1,480.50 · 07:45 · 36°C · 1/2 + 3/4 = 1¼"
		},
		{
			label: "Accents",
			text: "Łódź, Kraków, Škoda, Ærøskøbing, Târgu Mureș, Liepāja, Ōsaka"
		},
		{
			label: "Timetable",
			text:
				"The 8:15 to Central leaves from platform 4. Change at Union Square for the harbour line. Trains run every twelve minutes until midnight, then hourly until 5:00."
		}
	],

	// Weights. Each of the nine rows sets this line at its own weight.
	waterfall: "Skyline at dusk, 21 floors up",

	// Features. The words each demonstration is set in.
	ss01: "A salad of avocado and a banana",
	tnumRows: [
		["Rent", "1,200.00"],
		["Groceries", "348.17"],
		["Transit", "91.40"],
		["Total", "1,639.57"]
	],
	bracket: "$49 ¢99"
};
