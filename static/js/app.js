/**
 * Main Vue Router configuration for the dashboard shell.
 * Each component is registered globally by its own file
 * (static/js/components/*.js) onto window.Components before this file runs.
 */
const C = window.Components;

const routes = [
    { path: "/", component: C.EmployeeSummary },
    { path: "/activities", component: C.ActivityForm },
    { path: "/tasks", component: C.TaskList },
    { path: "/team", component: C.TeamPerformance },
    { path: "/approvals", component: C.Approvals },
    { path: "/audit-queue", component: C.AuditQueue },
    { path: "/assign-task", component: C.AssignTask },
    { path: "/heatmap", component: C.Heatmap },
    { path: "/admin/services", component: C.AdminServices },
    { path: "/admin/employees", component: C.AdminEmployees },
    { path: "/admin/distribution", component: C.AdminDistribution },
];

// "hash" mode is used (URLs like /#/team) so client-side routes don't need
// any additional Django URL configuration and work correctly on page refresh.
const router = new VueRouter({ mode: "hash", routes });

new Vue({
    el: "#app",
    router,
});
