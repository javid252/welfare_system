/**
 * Vue filters for displaying Jalali dates and Persian-digit numbers,
 * built entirely on the system's own conversion engine (static/js/jalali.js)
 * — independent of the browser's Intl/locale database.
 *
 *   {{ activity.date_performed | faDate }}     ->  ۱۴۰۵/۰۵/۰۶
 *   {{ activity.adjusted_swu | faNum(2) }}      ->  ۱۲٬۳۴۵٫۶۷
 *
 * requires static/js/jalali.js to be loaded first.
 */

function toJalaliDate(value) {
    if (!value) return "—";
    try {
        return window.Jalali.formatJalali(value);
    } catch (e) {
        return String(value);
    }
}

function toJalaliDateTime(value) {
    if (!value) return "—";
    // API datetimes look like "2026-07-29 14:05"; split off the date part
    // for Jalali conversion and keep the time part as-is (with Persian digits).
    const [datePart, timePart] = String(value).split(" ");
    const jalaliDate = toJalaliDate(datePart);
    return timePart ? `${jalaliDate} - ${window.Jalali.toFaDigits(timePart)}` : jalaliDate;
}

/** Groups an integer/decimal string with Persian thousand separators (٬). */
function groupDigits(numStr, decimals) {
    const negative = numStr.startsWith("-");
    if (negative) numStr = numStr.slice(1);
    let [intPart, fracPart] = numStr.split(".");
    intPart = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, "٬");
    let result = intPart;
    if (decimals !== undefined && decimals > 0) {
        fracPart = (fracPart || "").padEnd(decimals, "0").slice(0, decimals);
        result += "٫" + fracPart;
    } else if (fracPart) {
        result += "٫" + fracPart;
    }
    return (negative ? "-" : "") + result;
}

function toFaNumber(value, decimals) {
    if (value === null || value === undefined || value === "") return "—";
    const num = Number(value);
    if (isNaN(num)) return String(value);
    const fixed = decimals !== undefined ? num.toFixed(decimals) : String(num);
    return window.Jalali.toFaDigits(groupDigits(fixed, decimals));
}

window.PersianUtils = { toJalaliDate, toJalaliDateTime, toFaNumber };

if (window.Vue) {
    Vue.filter("faDate", toJalaliDate);
    Vue.filter("faDateTime", toJalaliDateTime);
    Vue.filter("faNum", toFaNumber);
}
