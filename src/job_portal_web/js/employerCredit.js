document.addEventListener("DOMContentLoaded", () => {

    const creditData = document.getElementById("credit-data");

    if (!creditData) return;

    const totalCredit = Number(
        creditData.dataset.totalCredit
    );

    const availableCredit = Number(
        creditData.dataset.availableCredit
    );

    const circle = document.getElementById("progress-ring");

    if (!circle) return;

    const radius = 70;

    const circumference = 2 * Math.PI * radius;

    circle.style.strokeDasharray = circumference;

    if (totalCredit <= 0) {

        circle.style.strokeDashoffset = circumference;

        return;

    }

    const percentage = availableCredit / totalCredit;

    circle.style.strokeDashoffset =
        circumference * (1 - percentage);

});