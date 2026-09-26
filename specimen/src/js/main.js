import "./assets.js";
import fontData from "../_data/fontdata.json";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const fontClasses = fontData.map(f => f.selector);
const [ROMAN, ITALIC] = fontClasses;

if (!(window.CSS && CSS.supports("font-variation-settings", '"wght" 100'))) {
	document.documentElement.classList.add("no-variable");
}

/* Toast ------------------------------------------------------------------ */

const toastEl = $(".toast");
let toastTimer;
const toast = message => {
	toastEl.textContent = message;
	toastEl.classList.add("is-shown");
	clearTimeout(toastTimer);
	toastTimer = setTimeout(() => toastEl.classList.remove("is-shown"), 1800);
};

// Plain promises: Babel would turn async/await into regenerator calls that
// this build has no runtime for.
const copy = (text, message) => {
	const fail = () => toast("Copy failed");
	if (!navigator.clipboard) return fail();
	// Guarded above, so browsers without the Clipboard API get the message.
	// eslint-disable-next-line compat/compat
	navigator.clipboard.writeText(text).then(() => toast(message), fail);
};

/* Theme ------------------------------------------------------------------ */

const themeBtn = $(".theme-toggle");
const isDark = () => {
	const set = document.documentElement.getAttribute("data-theme");
	return set
		? set === "dark"
		: window.matchMedia("(prefers-color-scheme: dark)").matches;
};
const labelTheme = () =>
	themeBtn.setAttribute(
		"aria-label",
		isDark() ? "Switch to light theme" : "Switch to dark theme"
	);
labelTheme();
themeBtn.addEventListener("click", () => {
	const next = isDark() ? "light" : "dark";
	document.documentElement.setAttribute("data-theme", next);
	try {
		localStorage.setItem("theme", next);
	} catch (e) {
		// Private mode: the choice lasts for this page only.
	}
	labelTheme();
});

/* Top bar: border once scrolled, and the current section highlighted. ----- */

const topbar = $(".topbar");
const onScroll = () =>
	topbar.classList.toggle("is-scrolled", window.scrollY > 8);
window.addEventListener("scroll", onScroll, { passive: true });
onScroll();

const navLinks = $$(".topbar-nav a");
if ("IntersectionObserver" in window) {
	const spy = new IntersectionObserver(
		entries => {
			for (const e of entries) {
				if (!e.isIntersecting) continue;
				for (const a of navLinks) {
					a.classList.toggle(
						"is-current",
						a.getAttribute("href") === `#${e.target.id}`
					);
				}
			}
		},
		{ rootMargin: "-45% 0px -50% 0px" }
	);
	for (const a of navLinks) {
		const target = $(a.getAttribute("href"));
		if (target) spy.observe(target);
	}
}

/* Range sliders: keep the fill and the bubble under the thumb. ------------ */

const syncRange = input => {
	const wrap = input.closest(".range");
	if (!wrap) return;
	const min = Number(input.min);
	const max = Number(input.max);
	wrap.style.setProperty("--f", (Number(input.value) - min) / (max - min));
	const bubble = $(".range-bubble", wrap);
	if (bubble) bubble.textContent = Math.round(input.value);
};

for (const input of $$('.range input[type="range"]')) {
	syncRange(input);
	input.addEventListener("input", () => syncRange(input));
	const wrap = input.closest(".range");
	input.addEventListener("pointerdown", () =>
		wrap.classList.add("is-active")
	);
	window.addEventListener("pointerup", () =>
		wrap.classList.remove("is-active")
	);
}

/* Named instances --------------------------------------------------------- */

const snapButtons = $$(".snap");
const instances = snapButtons.map(b => ({
	wght: Number(b.dataset.wght),
	name: b.getAttribute("aria-label").split(",")[0]
}));

const weightName = w => {
	const exact = instances.find(i => i.wght === w);
	if (exact) return exact.name;
	const nearest = instances.reduce((a, b) =>
		Math.abs(b.wght - w) < Math.abs(a.wght - w) ? b : a
	);
	return `≈ ${nearest.name}`;
};

/* Hero: letters swell toward the pointer; idle, a wave rolls through. ----- */

const heroWord = $(".hero-word");
const letters = $$(".hero-letter");
if (heroWord && letters.length) {
	const n = letters.length;
	const current = letters.map(() => 400);
	let focus = null; // pointer position in letter units, or null when idle
	let lastMove = 0;
	let visible = true;
	let raf = 0;

	const targetFor = (i, t) => {
		if (focus !== null) {
			const d = i + 0.5 - focus;
			return 100 + 800 * Math.exp(-(d * d) / 2.2);
		}
		if (reduceMotion.matches) return 400;
		// Idle: a soft wave sweeps back and forth across the word.
		const centre = (Math.sin(t / 1400) * 0.5 + 0.5) * (n + 4) - 2;
		const d = i + 0.5 - centre;
		return 250 + 550 * Math.exp(-(d * d) / 3);
	};

	const frame = t => {
		raf = 0;
		if (focus !== null && t - lastMove > 2500) focus = null;
		letters.forEach((el, i) => {
			const target = targetFor(i, t);
			current[i] +=
				(target - current[i]) * (reduceMotion.matches ? 1 : 0.14);
			el.style.setProperty("--wght", current[i].toFixed(1));
		});
		if (visible) raf = requestAnimationFrame(frame);
	};

	const start = () => {
		if (!raf) raf = requestAnimationFrame(frame);
	};

	heroWord.addEventListener("pointermove", e => {
		const r = heroWord.getBoundingClientRect();
		focus = clamp((e.clientX - r.left) / r.width, 0, 1) * n;
		lastMove = performance.now();
		start();
	});
	heroWord.addEventListener("pointerleave", () => {
		focus = null;
	});

	if ("IntersectionObserver" in window) {
		new IntersectionObserver(([e]) => {
			visible = e.isIntersecting;
			if (visible) start();
		}).observe(heroWord);
	}
	start();
}

/* Playground -------------------------------------------------------------- */

const pg = $("#playground");
const stage = $(".pg-stage", pg);
const text = $(".pg-text", pg);
const form = $(".pg-controls", pg);
const wght = $("#pg-wght");
const wghtNum = $("#pg-wght-num");
const readNum = $(".pg-readout-num", pg);
const readName = $(".pg-readout-name", pg);
const sampleChips = $$(".chip[data-sample]", pg);
const samples = $$("p", $("#samples").content).map(p => p.textContent);
const playBtn = $(".btn-play", pg);

const DEFAULTS = {
	wght: Number(wght.defaultValue),
	style: ROMAN,
	// Phones start smaller, so a pangram fits in the pinned stage.
	size: window.matchMedia("(max-width: 700px)").matches ? 28 : 45,
	leading: 1.1,
	tracking: 0,
	align: "left",
	ss01: false,
	tnum: false,
	scheme: "paper",
	sample: 0
};
const state = Object.assign({}, DEFAULTS);

const setRadio = (name, value) => {
	const input = form.querySelector(`input[name="${name}"][value="${value}"]`);
	if (input) input.checked = true;
};

const render = () => {
	const w = Math.round(state.wght);
	text.style.setProperty("--wght", state.wght);
	text.style.setProperty("--size", `${state.size}px`);
	text.style.setProperty("--leading", state.leading);
	text.style.setProperty("--tracking", `${state.tracking}em`);
	text.style.setProperty("--align", state.align);
	text.classList.remove(...fontClasses);
	text.classList.add(state.style);
	text.classList.toggle("ss01", state.ss01);
	text.classList.toggle("tnum", state.tnum);
	stage.dataset.scheme = state.scheme;

	wght.value = state.wght;
	if (document.activeElement !== wghtNum) wghtNum.value = w;
	const name = weightName(w);
	wght.setAttribute("aria-valuetext", `${w}, ${name.replace("≈", "near")}`);
	syncRange(wght);
	readNum.textContent = w;
	readName.textContent = name;
	for (const b of snapButtons)
		b.setAttribute("aria-pressed", String(Number(b.dataset.wght) === w));

	for (const [key, unit] of [
		["size", "px"],
		["leading", ""],
		["tracking", "em"]
	]) {
		const input = form.elements[key];
		input.value = state[key];
		syncRange(input);
		form.querySelector(
			`output[for="${input.id}"]`
		).textContent = `${state[key]}${unit}`;
	}
	setRadio("style", state.style);
	setRadio("align", state.align);
	setRadio("scheme", state.scheme);
	form.elements.ss01.checked = state.ss01;
	form.elements.tnum.checked = state.tnum;

	sampleChips.forEach((chip, i) => {
		const on = i === state.sample;
		chip.classList.toggle("is-active", on);
		chip.setAttribute("aria-pressed", String(on));
	});
};

/* The link carries everything except the text, so a shared link opens the
   same setting on the same sample. */
const KEYS = {
	wght: "w",
	size: "s",
	leading: "l",
	tracking: "t",
	align: "a",
	scheme: "c",
	sample: "x"
};
let urlTimer;
const writeUrl = () => {
	clearTimeout(urlTimer);
	urlTimer = setTimeout(() => {
		const p = new URLSearchParams();
		for (const [k, short] of Object.entries(KEYS)) {
			const v = state[k];
			if (v === DEFAULTS[k] || v === null) continue;
			p.set(
				short,
				typeof v === "number" ? String(Math.round(v * 100) / 100) : v
			);
		}
		if (state.style === ITALIC) p.set("i", "1");
		if (state.ss01) p.set("ss01", "1");
		if (state.tnum) p.set("tnum", "1");
		const qs = p.toString();
		history.replaceState(
			null,
			"",
			`${location.pathname}${qs ? `?${qs}` : ""}${location.hash}`
		);
	}, 250);
};

const readUrl = () => {
	const p = new URLSearchParams(location.search);
	const num = (short, lo, hi) =>
		p.has(short) && !isNaN(p.get(short))
			? clamp(Number(p.get(short)), lo, hi)
			: undefined;
	const set = (k, v) => {
		if (v !== undefined) state[k] = v;
	};
	set("wght", num("w", Number(wght.min), Number(wght.max)));
	set("size", num("s", 12, 220));
	set("leading", num("l", 0.8, 2));
	set("tracking", num("t", -0.08, 0.3));
	const sample = num("x", 0, samples.length - 1);
	set("sample", sample === undefined ? undefined : Math.round(sample));
	if (["left", "center", "right"].includes(p.get("a")))
		state.align = p.get("a");
	if (["paper", "ink", "citrus", "cobalt"].includes(p.get("c")))
		state.scheme = p.get("c");
	if (p.get("i") === "1") state.style = ITALIC;
	state.ss01 = p.get("ss01") === "1";
	state.tnum = p.get("tnum") === "1";
};

const update = patch => {
	Object.assign(state, patch);
	render();
	writeUrl();
};

let playing = false;
let playRaf = 0;
const stopPlay = () => {
	playing = false;
	cancelAnimationFrame(playRaf);
	playBtn.setAttribute("aria-pressed", "false");
	$(".btn-play-label", playBtn).textContent = "Animate weight";
};
const startPlay = () => {
	playing = true;
	playBtn.setAttribute("aria-pressed", "true");
	$(".btn-play-label", playBtn).textContent = "Pause";
	const min = Number(wght.min);
	const max = Number(wght.max);
	// Start the sweep from wherever the weight is now, heading up.
	const start =
		performance.now() -
		Math.asin(((state.wght - min) / (max - min)) * 2 - 1) * 1100;
	const tick = t => {
		if (!playing) return;
		const phase = (t - start) / 1100;
		state.wght = Math.round(
			min + (max - min) * (Math.sin(phase) * 0.5 + 0.5)
		);
		render();
		playRaf = requestAnimationFrame(tick);
	};
	playRaf = requestAnimationFrame(tick);
};
playBtn.addEventListener("click", () => {
	if (playing) {
		stopPlay();
		writeUrl();
	} else {
		startPlay();
	}
});

wght.addEventListener("input", () => {
	stopPlay();
	update({ wght: Number(wght.value) });
});
wghtNum.addEventListener("change", () => {
	stopPlay();
	const v = clamp(
		Math.round(Number(wghtNum.value) || state.wght),
		Number(wght.min),
		Number(wght.max)
	);
	wghtNum.value = v;
	update({ wght: v });
});
for (const b of snapButtons) {
	b.addEventListener("click", () => {
		stopPlay();
		update({ wght: Number(b.dataset.wght) });
	});
}

form.addEventListener("input", e => {
	const t = e.target;
	if (t === wght || t === wghtNum) return;
	if (t.type === "range") update({ [t.name]: Number(t.value) });
	else if (t.type === "radio") update({ [t.name]: t.value });
	else if (t.type === "checkbox") update({ [t.name]: t.checked });
});
form.addEventListener("submit", e => e.preventDefault());

sampleChips.forEach((chip, i) => {
	chip.addEventListener("click", () => {
		text.textContent = samples[i];
		update({ sample: i });
	});
});
text.addEventListener("input", () => {
	if (state.sample !== null) update({ sample: null });
});

$('[data-action="reset"]', form).addEventListener("click", () => {
	stopPlay();
	text.textContent = samples[0];
	Object.assign(state, DEFAULTS);
	render();
	writeUrl();
	toast("Reset");
});
$('[data-action="share"]', form).addEventListener("click", () => {
	clearTimeout(urlTimer);
	writeUrl();
	setTimeout(() => copy(location.href, "Link copied"), 300);
});

readUrl();
if (state.sample !== null && samples[state.sample])
	text.textContent = samples[state.sample];
render();

/* Weights ---------------------------------------------------------------- */

const wList = $(".w-list");
for (const r of $$('input[name="w-style"]')) {
	r.addEventListener("change", () => {
		wList.classList.remove(...fontClasses);
		wList.classList.add(r.value);
	});
}
for (const row of $$(".w-row")) {
	row.addEventListener("click", () => {
		stopPlay();
		const style = wList.classList.contains(ITALIC) ? ITALIC : ROMAN;
		update({ wght: Number(row.dataset.wght), style });
		pg.scrollIntoView({
			behavior: reduceMotion.matches ? "auto" : "smooth"
		});
		text.focus({ preventScroll: true });
	});
}

/* Features --------------------------------------------------------------- */

for (const card of $$('[data-demo="ss01"], [data-demo="tnum"]')) {
	const box = $('input[type="checkbox"]', card);
	box.addEventListener("change", () =>
		card.classList.toggle("is-on", box.checked)
	);
}

const bracket = $('[data-demo="bracket"]');
if (bracket) {
	const slider = $('input[type="range"]', bracket);
	const glyph = $(".card-glyph", bracket);
	const badge = $(".badge", bracket);
	const sync = () => {
		glyph.style.setProperty("--wght", slider.value);
		badge.textContent =
			Number(slider.value) >= 700
				? `Stubs · ${slider.value}`
				: `Full bar · ${slider.value}`;
	};
	slider.addEventListener("input", sync);
	sync();
}

/* Glyphs ----------------------------------------------------------------- */

const grid = $(".g-grid");
const inspector = $(".g-inspector");
const big = $(".g-big", inspector);
const cpLabel = $(".g-cp", inspector);
let currentCell = null;

const inspect = cell => {
	if (!cell || cell === currentCell) return;
	if (currentCell) currentCell.classList.remove("is-current");
	currentCell = cell;
	cell.classList.add("is-current");
	big.textContent = cell.textContent;
	cpLabel.textContent = `U+${cell.dataset.cp}`;
};

grid.addEventListener("pointerover", e => inspect(e.target.closest(".g-cell")));
grid.addEventListener("focusin", e => inspect(e.target.closest(".g-cell")));
grid.addEventListener("click", e => {
	const cell = e.target.closest(".g-cell");
	if (cell)
		copy(
			cell.textContent,
			`Copied ${cell.textContent}  U+${cell.dataset.cp}`
		);
});
inspect($(".g-cell", grid));

const gWght = $("#g-wght");
gWght.addEventListener("input", () => {
	inspector.style.setProperty("--wght", gWght.value);
	grid.style.setProperty("--wght", gWght.value);
	$('output[for="g-wght"]').textContent = gWght.value;
});
for (const r of $$('input[name="g-style"]')) {
	r.addEventListener("change", () => {
		for (const el of [grid, inspector]) {
			el.classList.remove(...fontClasses);
			el.classList.add(r.value);
			el.style.setProperty("--wght", gWght.value);
		}
	});
}

const filterChips = $$(".g-filters .chip");
for (const chip of filterChips) {
	chip.addEventListener("click", () => {
		const f = chip.dataset.filter;
		for (const c of filterChips) {
			c.classList.toggle("is-active", c === chip);
			c.setAttribute("aria-pressed", String(c === chip));
		}
		for (const cell of $$(".g-cell", grid))
			cell.hidden = f !== "all" && cell.dataset.group !== f;
		inspect($(".g-cell:not([hidden])", grid));
	});
}

/* Languages -------------------------------------------------------------- */

const langInput = $("#lang-q");
const langList = $(".lang-list");
const langItems = $$("li", langList);
const langResult = $("#lang-result");
const fold = s =>
	s
		.normalize("NFD")
		.replace(/[̀-ͯ]/g, "")
		.toLowerCase();
const langIndex = langItems.map(li => fold(li.textContent));
const langMore = $(".lang-more");
langMore.addEventListener("click", () => {
	const open = langList.classList.toggle("is-collapsed") === false;
	langMore.setAttribute("aria-expanded", String(open));
	langMore.textContent = open ? "Show fewer" : `Show all ${langItems.length}`;
});

langInput.addEventListener("input", () => {
	const q = fold(langInput.value.trim());
	langList.classList.toggle("is-filtering", q.length > 0);
	if (!q) {
		langResult.textContent = "";
		return;
	}
	let hits = 0;
	let first = null;
	langItems.forEach((li, i) => {
		const hit = langIndex[i].includes(q);
		li.classList.toggle("is-match", hit);
		if (hit) {
			hits += 1;
			first = first || li;
		}
	});
	langResult.textContent =
		hits === 0
			? "Not on the list. Paste some text into the type tester to check."
			: hits === 1
			? `Yes: ${first.textContent}.`
			: `${hits} matches.`;
});

/* Copy buttons ----------------------------------------------------------- */

for (const btn of $$("[data-copy]")) {
	btn.addEventListener("click", () =>
		copy($(btn.dataset.copy).textContent, "CSS copied")
	);
}

/* Reveal sections as they arrive, only when motion is welcome. ------------ */

if ("IntersectionObserver" in window && !reduceMotion.matches) {
	const io = new IntersectionObserver(
		entries => {
			for (const e of entries) {
				if (e.isIntersecting) {
					e.target.classList.add("is-in");
					io.unobserve(e.target);
				}
			}
		},
		{ rootMargin: "0px 0px -10% 0px" }
	);
	for (const el of $$(".section, .get")) {
		if (el.getBoundingClientRect().top > window.innerHeight) {
			el.classList.add("reveal");
			io.observe(el);
		}
	}
}
