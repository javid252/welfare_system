/**
 * <jalali-date-picker v-model="form.date_performed"></jalali-date-picker>
 *
 * A self-contained Jalali (Shamsi) calendar date-picker:
 *   - v-model binds an ISO 'YYYY-MM-DD' Gregorian string (so it drops
 *     straight into existing forms/API payloads without any backend change)
 *   - the displayed grid, month/year navigation, and digits are all Jalali
 *   - holidays/occasions are fetched from /api/holidays/resolved/ for the
 *     displayed Jalali year and shaded on the grid (red = official day off,
 *     amber = occasion), with the title shown as a tooltip
 *   - Fridays are shaded as the weekend
 *
 * Registered as a global Vue component so any other component's template
 * can use <jalali-date-picker> without extra wiring.
 */
Vue.component("jalali-date-picker", {
    props: {
        value: { type: String, default: null }, // ISO 'YYYY-MM-DD'
    },
    data() {
        const today = new Date();
        const [ty, tm] = window.Jalali.toJalaali(today.getFullYear(), today.getMonth() + 1, today.getDate());
        return {
            open: false,
            viewYear: ty,
            viewMonth: tm,
            holidays: {}, // { "jy-jm-jd": {title, is_day_off} }
            loadedYear: null,
            weekdayShort: window.Jalali.WEEKDAY_SHORT,
        };
    },
    computed: {
        selectedJalali() {
            return this.value ? window.Jalali.dateToJalali(this.value) : null;
        },
        displayValue() {
            return this.value ? window.Jalali.formatJalali(this.value) : "";
        },
        monthLabel() {
            return `${window.Jalali.MONTH_NAMES[this.viewMonth - 1]} ${window.Jalali.toFaDigits(this.viewYear)}`;
        },
        weeks() {
            const daysInMonth = window.Jalali.jalaliMonthLength(this.viewYear, this.viewMonth);
            const firstIso = window.Jalali.jalaliToIso(this.viewYear, this.viewMonth, 1);
            const firstWeekday = window.Jalali.jalaliWeekday(firstIso); // 0=Sat..6=Fri
            const cells = [];
            for (let i = 0; i < firstWeekday; i++) cells.push(null);
            for (let d = 1; d <= daysInMonth; d++) cells.push(d);
            while (cells.length % 7 !== 0) cells.push(null);
            const weeks = [];
            for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
            return weeks;
        },
    },
    mounted() {
        document.addEventListener("click", this.handleOutsideClick);
    },
    beforeDestroy() {
        document.removeEventListener("click", this.handleOutsideClick);
    },
    methods: {
        handleOutsideClick(e) {
            if (this.open && this.$el && !this.$el.contains(e.target)) {
                this.open = false;
            }
        },
        toggle() {
            this.open = !this.open;
            if (this.open) {
                if (this.selectedJalali) {
                    this.viewYear = this.selectedJalali[0];
                    this.viewMonth = this.selectedJalali[1];
                }
                this.ensureHolidaysLoaded();
            }
        },
        async ensureHolidaysLoaded() {
            if (this.loadedYear === this.viewYear) return;
            try {
                const res = await api.get("holidays/resolved/", { params: { jalali_year: this.viewYear } });
                const map = {};
                res.data.forEach(h => {
                    map[`${h.jalali_year}-${h.jalali_month}-${h.jalali_day}`] = h;
                });
                this.holidays = map;
                this.loadedYear = this.viewYear;
            } catch (e) {
                // Non-fatal: calendar still works without holiday shading.
                this.holidays = {};
            }
        },
        prevMonth() {
            if (this.viewMonth === 1) { this.viewMonth = 12; this.viewYear -= 1; }
            else this.viewMonth -= 1;
            this.ensureHolidaysLoaded();
        },
        nextMonth() {
            if (this.viewMonth === 12) { this.viewMonth = 1; this.viewYear += 1; }
            else this.viewMonth += 1;
            this.ensureHolidaysLoaded();
        },
        faDigits(n) {
            return window.Jalali.toFaDigits(n);
        },
        holidayFor(day) {
            if (!day) return null;
            return this.holidays[`${this.viewYear}-${this.viewMonth}-${day}`] || null;
        },
        dayClasses(day, colIndex) {
            const holiday = this.holidayFor(day);
            const selected = this.isSelected(day);
            return {
                "btn-primary": selected,
                "btn-outline-secondary": !selected && this.isToday(day),
                "text-danger fw-bold": !selected && (colIndex === 6 || (holiday && holiday.is_day_off)),
                "text-warning-emphasis fw-bold": !selected && holiday && !holiday.is_day_off,
            };
        },
        isSelected(day) {
            if (!day || !this.selectedJalali) return false;
            const [sy, sm, sd] = this.selectedJalali;
            return sy === this.viewYear && sm === this.viewMonth && sd === day;
        },
        isToday(day) {
            if (!day) return false;
            const today = new Date();
            const [ty, tm, td] = window.Jalali.toJalaali(today.getFullYear(), today.getMonth() + 1, today.getDate());
            return ty === this.viewYear && tm === this.viewMonth && td === day;
        },
        pick(day) {
            if (!day) return;
            const iso = window.Jalali.jalaliToIso(this.viewYear, this.viewMonth, day);
            this.$emit("input", iso);
            this.open = false;
        },
    },
    template: `
    <div class="jalali-datepicker position-relative">
        <div class="input-group" @click="toggle" style="cursor:pointer">
            <input type="text" class="form-control" readonly :value="displayValue" placeholder="انتخاب تاریخ" style="cursor:pointer">
            <span class="input-group-text bg-white">📅</span>
        </div>

        <div v-if="open" class="jalali-datepicker-popup card shadow" @click.stop>
            <div class="card-body p-2">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <button type="button" class="btn btn-sm btn-light" @click="prevMonth">‹</button>
                    <strong>{{ monthLabel }}</strong>
                    <button type="button" class="btn btn-sm btn-light" @click="nextMonth">›</button>
                </div>
                <table class="table table-sm table-borderless text-center mb-0 jalali-grid">
                    <thead>
                        <tr>
                            <th v-for="(w, i) in weekdayShort" :key="i" :class="{'text-danger': i === 6}">{{ w }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(week, wi) in weeks" :key="wi">
                            <td v-for="(day, di) in week" :key="di">
                                <button
                                    v-if="day"
                                    type="button"
                                    class="btn btn-sm w-100 jalali-day-btn"
                                    :class="dayClasses(day, di)"
                                    :title="holidayFor(day) ? holidayFor(day).title : ''"
                                    @click="pick(day)"
                                >{{ faDigits(day) }}</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `,
});
