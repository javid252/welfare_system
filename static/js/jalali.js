/**
 * Self-contained Gregorian <-> Jalali (Persian/Shamsi) calendar conversion.
 * Mirrors core/jalali_utils.py exactly so the frontend and backend always
 * agree, independent of any browser Intl/locale support.
 */
(function () {
    const BREAKS = [
        -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
        1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178,
    ];

    const PERSIAN_MONTH_NAMES = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ];
    const PERSIAN_WEEKDAY_NAMES = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"];
    const PERSIAN_WEEKDAY_SHORT = ["ش", "ی", "د", "س", "چ", "پ", "ج"];

    function div(a, b) { return Math.trunc(a / b); }
    function mod(a, b) { return a - div(a, b) * b; }

    function jalCal(jy) {
        const bl = BREAKS.length;
        const gy = jy + 621;
        let leapJ = -14;
        let jp = BREAKS[0];
        if (jy < jp || jy >= BREAKS[bl - 1]) throw new Error("Invalid Jalali year " + jy);

        let jm = jp, jump = 0;
        for (let i = 1; i < bl; i += 1) {
            jm = BREAKS[i];
            jump = jm - jp;
            if (jy < jm) break;
            leapJ = leapJ + div(jump, 33) * 8 + div(mod(jump, 33), 4);
            jp = jm;
        }
        let n = jy - jp;
        leapJ = leapJ + div(n, 33) * 8 + div(mod(n, 33) + 3, 4);
        if (mod(jump, 33) === 4 && jump - n === 4) leapJ += 1;

        const leapG = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150;
        const march = 20 + leapJ - leapG;

        if (jump - n < 6) n = n - jump + div(jump, 33) * 33;
        let leap = mod(mod(n + 1, 33) - 1, 4);
        if (leap === -1) leap = 4;

        return { leap, gy, march };
    }

    function g2d(gy, gm, gd) {
        let d = div((gy + div(gm - 8, 6) + 100100) * 1461, 4)
            + div(153 * mod(gm + 9, 12) + 2, 5)
            + gd - 34840408;
        d = d - div(div(gy + 100100 + div(gm - 8, 6), 100) * 3, 4) + 752;
        return d;
    }

    function d2g(jdn) {
        let j = 4 * jdn + 139361631;
        j = j + div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
        const i = div(mod(j, 1461), 4) * 5 + 308;
        const gd = div(mod(i, 153), 5) + 1;
        const gm = mod(div(i, 153), 12) + 1;
        const gy = div(j, 1461) - 100100 + div(8 - gm, 6);
        return { gy, gm, gd };
    }

    function j2d(jy, jm, jd) {
        const r = jalCal(jy);
        return g2d(r.gy, 3, r.march) + (jm - 1) * 31 - div(jm, 7) * (jm - 7) + jd - 1;
    }

    function d2j(jdn) {
        const gy = d2g(jdn).gy;
        let jy = gy - 621;
        const r = jalCal(jy);
        const jdn1f = g2d(r.gy, 3, r.march);
        let k = jdn - jdn1f;
        if (k >= 0) {
            if (k <= 185) {
                return { jy, jm: 1 + div(k, 31), jd: mod(k, 31) + 1 };
            }
            k -= 186;
        } else {
            jy -= 1;
            k += 179;
            if (r.leap === 1) k += 1;
        }
        return { jy, jm: 7 + div(k, 30), jd: mod(k, 30) + 1 };
    }

    function toJalaali(gy, gm, gd) {
        const r = d2j(g2d(gy, gm, gd));
        return [r.jy, r.jm, r.jd];
    }

    function toGregorian(jy, jm, jd) {
        const r = d2g(j2d(jy, jm, jd));
        return [r.gy, r.gm, r.gd];
    }

    function isLeapJalaliYear(jy) {
        return jalCal(jy).leap === 0;
    }

    function jalaliMonthLength(jy, jm) {
        if (jm <= 6) return 31;
        if (jm <= 11) return 30;
        return isLeapJalaliYear(jy) ? 30 : 29;
    }

    const FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹";
    function toFaDigits(value) {
        return String(value).replace(/[0-9]/g, (d) => FA_DIGITS[d]);
    }
    function toEnDigits(value) {
        return String(value).replace(/[۰-۹]/g, (d) => FA_DIGITS.indexOf(d));
    }

    /** Gregorian Date object (or 'YYYY-MM-DD' string) -> [jy, jm, jd] */
    function dateToJalali(dateOrStr) {
        const d = dateOrStr instanceof Date ? dateOrStr : new Date(dateOrStr + "T00:00:00");
        return toJalaali(d.getFullYear(), d.getMonth() + 1, d.getDate());
    }

    /** [jy, jm, jd] -> ISO 'YYYY-MM-DD' Gregorian string (for sending to the API) */
    function jalaliToIso(jy, jm, jd) {
        const [gy, gm, gd] = toGregorian(jy, jm, jd);
        return `${String(gy).padStart(4, "0")}-${String(gm).padStart(2, "0")}-${String(gd).padStart(2, "0")}`;
    }

    /** ISO/Date -> formatted Persian-digit Jalali string, e.g. ۱۴۰۵/۰۵/۰۶ */
    function formatJalali(dateOrStr) {
        if (!dateOrStr) return "—";
        const [jy, jm, jd] = dateToJalali(dateOrStr);
        return toFaDigits(`${jy}/${String(jm).padStart(2, "0")}/${String(jd).padStart(2, "0")}`);
    }

    /** Weekday index (0=Saturday .. 6=Friday) for a Gregorian Date/ISO string. */
    function jalaliWeekday(dateOrStr) {
        const d = dateOrStr instanceof Date ? dateOrStr : new Date(dateOrStr + "T00:00:00");
        return (d.getDay() + 1) % 7; // JS: Sun=0..Sat=6  ->  Sat=0..Fri=6
    }

    window.Jalali = {
        toJalaali, toGregorian, isLeapJalaliYear, jalaliMonthLength,
        toFaDigits, toEnDigits, dateToJalali, jalaliToIso, formatJalali, jalaliWeekday,
        MONTH_NAMES: PERSIAN_MONTH_NAMES,
        WEEKDAY_NAMES: PERSIAN_WEEKDAY_NAMES,
        WEEKDAY_SHORT: PERSIAN_WEEKDAY_SHORT,
    };
})();
