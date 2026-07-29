window.Components = window.Components || {};

window.Components.AdminEmployees = {
    template: `
    <div>
        <h4 class="mb-4">مدیریت کارمندان و ضرایب منطقه</h4>

        <div class="card mb-4">
            <div class="card-header fw-bold">{{ editing ? 'ویرایش کارمند' : 'افزودن کارمند جدید' }}</div>
            <div class="card-body">
                <form @submit.prevent="save" class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">نام کاربری</label>
                        <input class="form-control" v-model="form.username" required :disabled="!!editing">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">کد پرسنلی</label>
                        <input class="form-control" v-model="form.employee_code" required>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">نام</label>
                        <input class="form-control" v-model="form.first_name">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">نام خانوادگی</label>
                        <input class="form-control" v-model="form.last_name">
                    </div>

                    <div class="col-md-3">
                        <label class="form-label">نقش سازمانی</label>
                        <select class="form-select" v-model="form.role">
                            <option value="EMPLOYEE">کارمند</option>
                            <option value="SUPERVISOR">سرپرست شهرستان</option>
                            <option value="PROVINCIAL_MANAGER">مدیر استانی</option>
                            <option value="ADMIN">کمیته ملی (ادمین)</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">کد شهرستان</label>
                        <input class="form-control" v-model="form.region_code" required>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">کد استان</label>
                        <input class="form-control" v-model="form.province_code">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">ضریب منطقه</label>
                        <input type="number" step="0.05" min="0.1" max="3" class="form-control" v-model.number="form.region_coefficient">
                    </div>

                    <div class="col-md-3">
                        <label class="form-label">سرپرست مستقیم</label>
                        <select class="form-select" v-model="form.supervisor">
                            <option :value="null">— بدون سرپرست —</option>
                            <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }} ({{ e.employee_code }})</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">سمت سازمانی</label>
                        <input class="form-control" v-model="form.position">
                    </div>
                    <div class="col-md-3 d-flex align-items-end">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" v-model="form.is_multitasking" id="isMulti">
                            <label class="form-check-label" for="isMulti">چندوظیفه‌ای</label>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">ضریب چندوظیفگی</label>
                        <input type="number" step="0.05" min="1" max="2" class="form-control" v-model.number="form.multitasking_coefficient" :disabled="!form.is_multitasking">
                    </div>

                    <div class="col-12">
                        <button class="btn btn-primary">{{ editing ? 'ذخیره تغییرات' : 'افزودن (رمز اولیه = کد پرسنلی)' }}</button>
                        <button v-if="editing" type="button" class="btn btn-outline-secondary ms-2" @click="resetForm">انصراف</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead><tr><th>کد پرسنلی</th><th>نام</th><th>نقش</th><th>شهرستان</th><th>سرپرست</th><th></th></tr></thead>
                <tbody>
                    <tr v-for="e in employees" :key="e.id">
                        <td>{{ e.employee_code }}</td>
                        <td>{{ e.full_name }}</td>
                        <td>{{ roleLabel(e.role) }}</td>
                        <td>{{ e.region_code }}</td>
                        <td>{{ e.supervisor_name || '—' }}</td>
                        <td><button class="btn btn-sm btn-outline-primary" @click="edit(e)">ویرایش</button></td>
                    </tr>
                    <tr v-if="!employees.length"><td colspan="6" class="text-center text-muted py-3">کارمندی ثبت نشده است.</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return { employees: [], editing: null, form: this.blankForm() };
    },
    mounted() { this.load(); },
    methods: {
        blankForm() {
            return {
                username: "", employee_code: "", first_name: "", last_name: "",
                role: "EMPLOYEE", region_code: "", province_code: "",
                region_coefficient: 1.0, supervisor: null, position: "",
                is_multitasking: false, multitasking_coefficient: 1.0,
            };
        },
        roleLabel(r) {
            return { EMPLOYEE: "کارمند", SUPERVISOR: "سرپرست شهرستان", PROVINCIAL_MANAGER: "مدیر استانی", ADMIN: "کمیته ملی" }[r] || r;
        },
        async load() {
            const res = await api.get("employees/");
            this.employees = res.data.results || res.data;
        },
        edit(e) {
            this.editing = e.id;
            this.form = { ...e };
        },
        resetForm() {
            this.editing = null;
            this.form = this.blankForm();
        },
        async save() {
            if (this.editing) {
                await api.patch(`employees/${this.editing}/`, this.form);
            } else {
                await api.post("employees/", this.form);
            }
            this.resetForm();
            await this.load();
        },
    },
};
