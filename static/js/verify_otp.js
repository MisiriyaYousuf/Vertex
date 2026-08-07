document.addEventListener("DOMContentLoaded", () => {

    const otpInput = document.querySelector("#id_otp");

    if (otpInput) {
        otpInput.focus();

        otpInput.addEventListener("input", function () {
            this.value = this.value.replace(/\D/g, "");

            if (this.value.length > 6) {
                this.value = this.value.slice(0, 6);
            }
        });
    }

    if (!otpExpiresAt) return;

    const countdown = document.getElementById("countdown");
    const submitBtn = document.querySelector("button[type='submit']");
    const resendLink = document.getElementById("resendLink");

    function updateTimer() {

        const now = new Date();
        const expiry = new Date(otpExpiresAt);

        let diff = Math.floor((expiry - now) / 1000);

        if (diff <= 0) {

            const otpTimer = document.getElementById("otpTimer");
            otpTimer.textContent = "otp has been expired.";
            otpTimer.style.color = "#dc3545";

            if (otpInput) otpInput.disabled = true;
            if (submitBtn) submitBtn.disabled = true;

            if (resendLink) {
                resendLink.style.display = "inline";
            }

            clearInterval(interval);
            return;
        }

        const minutes = String(Math.floor(diff / 60)).padStart(2, "0");
        const seconds = String(diff % 60).padStart(2, "0");

        countdown.textContent = `${minutes}:${seconds}`;
    }

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.opacity = "0";

            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 3000);
    });

});

