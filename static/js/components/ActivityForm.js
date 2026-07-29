window.Components = window.Components || {};

window.Components.ActivityForm = {
    template: `
    <div>
        <div class="row g-4">
            <div class="col-lg-5">
                <div class="card">
                    <div class="card-header fw-bold">ثبت فعالیت جدید</div>
                    <div class="card-body">
                        <form @submit.prevent="submit">
                            <div class="mb-3">
                                <label class="form-label">خدمت</label>
                                <select class="form-select" v-model="form.service" required>
                                    <option disabled value="">انتخاب کنید...</option>
                                    <option v-for="s in services" :key="s.id" :value="s.id">
                                        {{ s.service_code }} — {{ s.name }} (واحد پایه: {{ s.base_swu | faNum(2) }})
                                    </option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">تاریخ انجام</label>
                                <jalali-date-picker v-model="form.date_performed"></jalali-date-picker>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">تعداد</label>
                                <input type="number" min="1" class="form-control" v-model.number="form.quantity" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">ضریب پیچیدگی درخواستی (نیازمند تایید سرپرست)</label>
                                <input type="number" step="0.1" min="1" max="3" class="form-control" v-model.number="form.complexity_coefficient">
                            </div>

                            <div class="alert alert-secondary">
                                <div class="d-flex justify-content-between">
                                    <span>پیش‌نمایش واحد کار پایه:</span>
                                    <strong>{{ previewBase | faNum(2) }}</strong>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <span>پیش‌نمایش واحد کار تعدیل‌شده (پس از تایید سرپرست):</span>
                                    <strong>{{ previewAdjusted | faNum(2) }}</strong>
                                </div>
                                <div class="form-text">
                                    فرمول: پایه × ضریب‌منطقه ({{ profile.region_coefficient | faNum(2) }}) × ضریب چندوظیفگی ({{ effectiveMultitasking | faNum(2) }}) × ضریب پیچیدگی تاییدشده
                                </div>
                            </div>

                            <div v-if="error" class="alert alert-danger">{{ error }}</div>
                            <button class="btn btn-primary w-100" :disabled="submitting">ثبت فعالیت</button>
                        </form>
                    </div>
                </div>
            </div>

            <div class="col-lg-7">
                <div class="card">
                    <div class="card-header fw-bold">تاریخچه فعالیت‌های من</div>
                    <div class="table-responsive">
                        <table class="table table-sm table-hover mb-0">
                            <thead>
                                <tr>
                                    <th>تاریخ</th><th>خدمت</th><th>تعداد</th>
                                    <th>واحد پایه</th><th>واحد تعدیل‌شده</th><th>وضعیت</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="a in activities" :key="a.id">
                                    <td>{{ a.date_performed | faDate }}</td>
                                    <td>{{ a.service_detail.name }}</td>
                                    <td>{{ a.quantity | faNum(0) }}</td>
                                    <td>{{ a.base_swu_total | faNum(2) }}</td>
                                    <td>{{ a.adjusted_swu | faNum(2) }}</td>
                                    <td>
                                        <span class="badge" :class="statusBadge(a.status)">{{ statusLabel(a.status) }}</span>
                                        <span v-if="a.complexity_coefficient > 1 && !a.is_complexity_approved"
                                              class="badge bg-warning text-dark ms-1">در انتظار تایید پیچیدگی</span>
                                    </td>
                                </tr>
                                <tr v-if="!activities.length"><td colspan="6" class="text-center text-muted py-3">فعالیتی ثبت نشده است.</td></tr>
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
            services: [],
            activities: [],
            profile: { region_coefficient: 1, is_multitasking: false, multitasking_coefficient: 1 },
            error: null,
            submitting: false,
            form: {
                service: "",
                date_performed: new Date().toISOString().slice(0, 10),
                quantity: 1,
                complexity_coefficient: 1,
            },
        };
    },
    computed: {
        selectedService() {
            return this.services.find(s => s.id === this.form.service);
        },
        effectiveMultitasking() {
            return this.profile.is_multitasking ? this.profile.multitasking_coefficient : 1;
        },
        previewBase() {
            const base = this.selectedService ? this.selectedService.base_swu : 0;
            return base * (this.form.quantity || 0);
        },
        previewAdjusted() {
            return this.previewBase
                * (this.form.complexity_coefficient || 1)
                * this.profile.region_coefficient
                * this.effectiveMultitasking;
        },
    },
    mounted() {
        this.loadAll();
    },
    methods: {
        statusLabel(s) {
            return { PENDING: "در انتظار تایید", APPROVED: "تایید شده", REJECTED: "رد شده" }[s] || s;
        },
        statusBadge(s) {
            return { PENDING: "bg-secondary", APPROVED: "bg-success", REJECTED: "bg-danger" }[s] || "bg-secondary";
        },
        async loadAll() {
            const [servicesRes, profileRes, activitiesRes] = await Promise.all([
                api.get("services/", { params: { is_active: true } }),
                api.get("auth/profile/"),
                api.get("activities/"),
            ]);
            this.services = servicesRes.data.results || servicesRes.data;
            this.profile = profileRes.data;
            this.activities = activitiesRes.data.results || activitiesRes.data;
        },
        async submit() {
            this.error = null;
            this.submitting = true;
            try {
                await api.post("activities/", this.form);
                this.form.quantity = 1;
                this.form.complexity_coefficient = 1;
                await this.loadAll();
            } catch (e) {
                this.error = "ثبت فعالیت با خطا مواجه شد. لطفاً ورودی‌ها را بررسی کنید.";
            } finally {
                this.submitting = false;
            }
        },
    },
};
