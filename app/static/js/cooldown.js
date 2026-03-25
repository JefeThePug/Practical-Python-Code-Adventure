document.addEventListener("DOMContentLoaded", () => {
    const boxes = document.querySelectorAll(".form-box:not(#access)");

    let form = null;
    let btn = null;

    for (const candidate of boxes) {
        const candidateForm = candidate.closest("form");
        const candidateBtn = candidateForm?.querySelector("button");

        if (candidateForm && candidateBtn) {
            form = candidateForm;
            btn = candidateBtn;
            break;
        }
    }

    if (!form || !btn) {
        console.log("No valid form-box with submit button found");
        return;
    }

    // 🔽 use server-provided cooldown
    if (SERVER_COOLDOWN > 0) {
        const until = Date.now() + SERVER_COOLDOWN * 1000;
        startCooldown(btn, until);
    }
});

function startCooldown(btn, until) {
    btn.disabled = true;

    const update = () => {
        const remaining = Math.ceil((until - Date.now()) / 1000);

        if (remaining <= 0) {
            btn.disabled = false;
            btn.textContent = "Submit";
            return true;
        }

        btn.textContent = `Wait ${remaining}s`;
        return false;
    };

    if (!update()) {
        const interval = setInterval(() => {
            if (update()) clearInterval(interval);
        }, 1000);
    }
}