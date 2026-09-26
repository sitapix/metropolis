module.exports = {
	extends: ["stylelint-config-standard", "stylelint-config-prettier"],
	plugins: ["stylelint-no-unsupported-browser-features"],
	rules: {
		"selector-id-pattern": [
			"^([a-z][a-z0-9]*)(-[a-z0-9]+)*$",
			{
				message:
					"Selector should use lowercase and separate words with hyphens (selector-class-pattern)"
			}
		],
		"selector-class-pattern": [
			"^([a-z][a-z0-9]*)(-[a-z0-9]+)*$",
			{
				message:
					"Selector should use lowercase and separate words with hyphens (selector-class-pattern)"
			}
		],
		indentation: "tab",
		// stylelint 12 predates aspect-ratio, which every current browser has.
		"property-no-unknown": [true, { ignoreProperties: ["aspect-ratio"] }],
		// Component rules are grouped by component, not sorted by specificity.
		"no-descending-specificity": null,
		"selector-pseudo-class-no-unknown": [
			true,
			{
				ignorePseudoClasses: ["global"]
			}
		],
		"plugin/no-unsupported-browser-features": [
			true,
			{
				severity: "warning",
				ignore: ["font-unicode-range", "css-resize", "css-appearance"]
			}
		]
	}
};
