window.Components = window.Components || {};

window.Components.AdminDistribution = {
    template: `
    <div>
        <h4 class="mb-4">اجرای توزیع رفاهی سالانه</h4>

        <div class="row g-4">
            <div class="col-lg-5">
                <div class="card mb-4">
                    <div class="card-header fw-bold">بودجه سالانه رفاهی</div>
                    <div class="card-body">
                        <form @submit.prevent="saveBudget" class="row g-3">
                            <div class="col-6">
                                <label class="form-label">سال</label>
                                <input type="number" class="form-control" v-model.number="budgetForm.year" required>
                            </div>
                            <div class="col-6">
                                <label class="form-label">بودجه کل (ریال)</label>
                                <input type="number" class="form-control" v-model.number="budgetForm.total_budget" required>
                            </div>
                            <div class="col-6">
                                <label class="form-label">ذخیره موارد خاص (ریال)</label>
                                <input type="number" class="form-control" v-model.number="budgetForm.reserved_fund">
                            </div>
                            <div class="col-12">
                                <button class="btn btn-outline-primary w-100">ثبت / به‌روزرسانی بودجه</button>
                            </div>
                        </form>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header fw-bold">اجرای محاسبات</div>
                    <div class="card-body d-grid gap-2">
                        <div class="mb-2">
                            <label class="form-label">سال مورد محاسبه</label>
                            <input type="number" class="form-control" v-model.number="year">
                        </div>
                        <button class="btn btn-outline-secondary" @click="runAuditSampling">
                            ۱. انتخاب نمونه ۵٪ ممیزی کیفیت
                        </button>
                        <button class="btn btn-primary" @click="runDistribution">
                            ۲. اجرای محاسبه و توزیع نهایی بودجه
                        </button>
                        <div v-if="message" class="alert alert-success mt-2 mb-0">{{ message }}</div>
                        <div v-if="error" class="alert alert-danger mt-2 mb-0">{{ error }}</div>
                    </div>
                </div>
            </div>

            <div class="col-lg-7">
                <div class="card">
                    <div class="card-header fw-bold">نتایج توزیع</div>
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead><tr><th>کارمند</th><th>واحد کار تعدیل‌شده سالانه</th><th>سهم محاسبه‌شده (ریال)</th><th>پرداخت‌شده</th></tr></thead>
                            <tbody>
                                <tr v-for="d in results" :key="d.id">
                                    <td>{{ d.employee_detail.full_name }} ({{ d.employee_detail.employee_code }})</td>
                                    <td>{{ d.annual_adjusted_swu | faNum(2) }}</td>
                                    <td>{{ d.distribution_share | faNum(0) }}</td>
                                    <td>
                                        <span class="badge" :class="d.paid ? 'bg-success' : 'bg-secondary'">{{ d.paid ? 'بله' : 'خیر' }}</span>
                                    </td>
                                </tr>
                                <tr v-if="!results.length"><td colspan="4" class="text-center text-muted py-3">نتیجه‌ای موجود نیست.</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            year: new Date().getFullYear(),
            budgetForm: { year: new Date().getFullYear(), total_budget: 0, reserved_fund: 0 },
            results: [],
            message: null,
            error: null,
        };
    },
    mounted() { this.loadResults(); },
    methods: {
        async saveBudget() {
            this.error = null;
            try {
                await api.post("budgets/", this.budgetForm);
                this.message = "بودجه با موفقیت ثبت شد.";
            } catch (e) {
                this.error = "ثبت بودجه با خطا مواجه شد (شاید بودجه این سال قبلاً ثبت شده — از پنل جنگو ادمین ویرایش کنید).";
            }
        },
        async runAuditSampling() {
            this.error = null;
            const res = await api.post("distribution/select-audit-sample/", { year: this.year });
            this.message = `${res.data.flagged_count} فعالیت برای ممیزی کیفیت انتخاب شد.`;
        },
        async runDistribution() {
            this.error = null;
            try {
                const res = await api.post("distribution/run/", { year: this.year });
                this.message = `توزیع رفاهی سال ${res.data.year} برای ${res.data.employees_paid_count} کارمند محاسبه شد.`;
                await this.loadResults();
            } catch (e) {
                this.error = (e.response && e.response.data && e.response.data.detail) || "محاسبه با خطا مواجه شد.";
            }
        },
        async loadResults() {
            const res = await api.get("distribution/", { params: { year: this.year } });
            this.results = res.data.results || res.data;
        },
    },
};
