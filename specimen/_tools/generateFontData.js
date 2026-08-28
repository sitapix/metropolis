// Copyright 2019 Google LLC

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

// 	https://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const fs = require("fs");
const util = require("util");
const path = require("path");
const fontkit = require("fontkit");
const {
	parseFontFile,
	buildStylesheet,
	getSelector,
	suggestFontStyle
} = require("specimen-skeleton-support");

const srcDirectory = path.resolve(__dirname, "../", "src");
const fontsDirectory = path.resolve(srcDirectory, "fonts");
const dataDirectory = path.resolve(srcDirectory, "_data/fonts");
const metaDataPath = path.resolve(srcDirectory, "_data/", "fontdata.json");
const fontsStylesheetPath = path.resolve(srcDirectory, "css", "fonts.css");

const assert = (condition, message) => {
	if (!condition) {
		throw new Error(message);
	}
};

const _appendFile = util.promisify(fs.appendFile);
const _writeFile = util.promisify(fs.writeFile);
const writeFile = (path, contents, append) => {
	console.info("Writing", path);
	if (append) {
		return _appendFile(path, contents);
	}
	return _writeFile(path, contents);
};

const writeDataFile = async (filename, fontName, data) => {
	fs.mkdir(path.join(dataDirectory, fontName), { recursive: true }, () => {
		const dataFilePath = path.join(dataDirectory, fontName, filename);
		const fileContents = JSON.stringify(data, null, 4);
		return writeFile(dataFilePath, fileContents);
	});
};

const writeDataFiles = async fontData => {
	const promises = Object.entries(fontData.data).map(([type, data]) => {
		return writeDataFile(`${type}.json`, getSelector(fontData, true), data);
	});

	return Promise.all(promises);
};

const writeStylesheet = async (fontData, fontFilePath) => {
	const fontUrl = path.relative(
		path.dirname(fontsStylesheetPath),
		fontFilePath
	);
	let stylesheet = buildStylesheet(fontData, fontUrl).toString();
	stylesheet += "\n\n";
	return writeFile(fontsStylesheetPath, stylesheet, true);
};

const findFontFile = async directory => {
	const fontFiles = (await util.promisify(fs.readdir)(directory)).filter(
		f => path.extname(f) == ".woff2"
	);

	assert(
		fontFiles.length > 0,
		`No WOFF2 font files found. Place your WOFF2 fonts in ${path.relative(
			process.cwd(),
			directory
		)}.`
	);

	const paths = fontFiles.map(fontFile => ({
		name: path.basename(fontFile, path.extname(fontFile)),
		path: path.resolve(fontsDirectory, fontFile)
	}));

	return paths;
};

// fontkit files name records below ID 256 under a string key -- ID 2 becomes
// `fontSubfamily` -- but resolves an fvar instance's name through the numeric
// key. An instance pointing at ID 2 or 17 therefore resolves to undefined and
// `namedVariations` throws reading `.en` off it. The OpenType spec asks for
// exactly that pointer: "If an instance record is included for the default
// instance ... then the nameID value should be set to 2 or 17 or to a name ID
// with the same value as name ID 2 or 17." Metropolis follows it, as does every
// variable font macOS ships. Resolve those two IDs here.
// https://learn.microsoft.com/en-us/typography/opentype/spec/fvar
const STANDARD_NAME_KEYS = { 2: "fontSubfamily", 17: "preferredSubfamily" };

const instanceName = (font, instance) => {
	const record =
		instance.name || font.name.records[STANDARD_NAME_KEYS[instance.nameID]];
	assert(
		record,
		`fvar instance at ${instance.coord} names no string in the name table (name ID ${instance.nameID}).`
	);
	return record[fontkit.defaultLanguage] || Object.values(record)[0];
};

const patchNamedVariations = fontPath => {
	let proto = Object.getPrototypeOf(fontkit.openSync(fontPath));
	while (proto && !Object.getOwnPropertyDescriptor(proto, "namedVariations")) {
		proto = Object.getPrototypeOf(proto);
	}
	assert(proto, "fontkit no longer defines namedVariations; drop this patch.");

	Object.defineProperty(proto, "namedVariations", {
		get() {
			const variations = {};
			if (!this.fvar) {
				return variations;
			}
			for (const instance of this.fvar.instance) {
				const settings = {};
				this.fvar.axis.forEach((axis, i) => {
					settings[axis.axisTag.trim()] = instance.coord[i];
				});
				variations[instanceName(this, instance)] = settings;
			}
			return variations;
		}
	});
};

// `fontdata.json` is meant to be hand-edited -- the order sets the font tree and
// the tester dropdown, and the style is guessed from the filename, so
// `Metropolis[wght].woff2` comes out as "unknown" -- but a regenerate overwrites
// it. Carry the committed order and style across, keyed by selector. `name` is
// deliberately not carried: fonts.css and the FontFaceObserver in main.js both
// key off it, so an edited one silently fails to load.
const mergeMetaData = (generated, committed) => {
	const order = committed.map(font => font.selector);
	const styles = new Map(committed.map(font => [font.selector, font.style]));
	const rank = font => {
		const i = order.indexOf(font.selector);
		return i === -1 ? order.length : i;
	};

	return generated
		.map(font => ({ ...font, style: styles.get(font.selector) || font.style }))
		.sort((a, b) => rank(a) - rank(b));
};

const readMetaData = () => {
	try {
		return JSON.parse(fs.readFileSync(metaDataPath, "utf8"));
	} catch (e) {
		if (e.code !== "ENOENT") throw e;
		return [];
	}
};

const getMetaData = (fontData, fontFile) => {
	return {
		name: fontData.name,
		selector: getSelector(fontData, true),
		style: suggestFontStyle(fontFile.name)
	};
};

const main = async () => {
	const fontFiles = process.argv[2] || (await findFontFile(fontsDirectory));
	const committedMetaData = readMetaData();
	patchNamedVariations(fontFiles[0].path);

	// Clear out old data files
	console.log("Deleting old data files");
	// `fs.rmdirSync(path, { recursive: true })`, which upstream calls, throws
	// ERR_INVALID_ARG_VALUE from Node 16 on.
	fs.rmSync(dataDirectory, { recursive: true, force: true });

	// Initialise files
	writeFile(
		fontsStylesheetPath,
		`/* Generated by the Specimen Skeleton */\n`
	);

	let metaData = [];
	for (const fontFile of fontFiles) {
		const fontData = await parseFontFile(fontFile.path);
		metaData.push(await getMetaData(fontData, fontFile));
		await Promise.all([
			writeDataFiles(fontData),
			writeStylesheet(fontData, fontFile.path)
		]);
	}

	const fileContents = JSON.stringify(
		mergeMetaData(metaData, committedMetaData),
		null,
		4
	);
	writeFile(metaDataPath, fileContents);
};

main().catch(e => {
	process.exitCode = 1;
	console.error("Failed to generate font data.", e);
});
