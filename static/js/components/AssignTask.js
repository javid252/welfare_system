window.Components = window.Components || {};

window.Components.AssignTask = {
    template: `
    <div class="row justify-content-center">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header fw-bold">تخصیص وظیفه جدید</div>
                <div class="card-body">
                    <form @submit.prevent="submit">
                        <div class="mb-3">
                            <label class="form-label">مسئول انجام</label>
                            <select class="form-select" v-model="form.assigned_to" required>
                                <option disabled value="">انتخاب کنید...</option>
                                <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }} ({{ e.employee_code }})</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">خدمت مرتبط</label>
                            <select class="form-select" v-model="form.service" required>
                                <option disabled value="">انتخاب کنید...</option>
                                <option v-for="s in services" :key="s.id" :value="s.id">{{ s.name }}</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">شرح وظیفه</label>
                            <textarea class="form-control" v-model="form.description" rows="3"></textarea>
                        </div>
                        <div class="row">
                            <div class="col-6 mb-3">
                                <label class="form-label">اولویت</label>
                                <select class="form-select" v-model="form.priority">
                                    <option value="LOW">کم</option>
                                    <option value="MEDIUM">متوسط</option>
                                    <option value="HIGH">بالا</option>
                                </select>
                            </div>
                            <div class="col-6 mb-3">
                                <label class="form-label">مهلت انجام</label>
                                <jalali-date-picker v-model="form.deadline"></jalali-date-picker>
                            </div>
                        </div>
                        <div v-if="success" class="alert alert-success">وظیفه با موفقیت تخصیص یافت.</div>
                        <button class="btn btn-primary w-100">تخصیص وظیفه</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            employees: [], services: [], success: false,
            form: { assigned_to: "", service: "", description: "", priority: "MEDIUM", deadline: "" },
        };
    },
    mounted() { this.load(); },
    methods: {
        async load() {
            const [empRes, svcRes] = await Promise.all([api.get("employees/"), api.get("services/")]);
            this.employees = empRes.data.results || empRes.data;
            this.services = svcRes.data.results || svcRes.data;
        },
        async submit() {
            await api.post("tasks/", this.form);
            this.success = true;
            this.form = { assigned_to: "", service: "", description: "", priority: "MEDIUM", deadline: "" };
            setTimeout(() => { this.success = false; }, 3000);
        },
    },
};
