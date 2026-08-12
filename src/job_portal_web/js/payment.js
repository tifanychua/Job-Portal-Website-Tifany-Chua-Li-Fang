// =========================================
// Render PayPal Button
// =========================================

paypal.Buttons({

    // =====================================
    // Create Order
    // =====================================

    createOrder: async function () {

        const response = await fetch(
            `/paypal/create-order/${packageName}`,
            {
                method: "POST"
            }
        );

        if (!response.ok) {

            const error = await response.text();

            alert(error);

            throw new Error(error);

        }

        const data = await response.json();

        return data.id;

    },

    // =====================================
    // Payment Approved
    // =====================================

    onApprove: async function (data) {

        const response = await fetch(

            `/paypal/capture-order/${data.orderID}`,

            {
                method: "POST"
            }

        );

        const result = await response.json();

        if (result.success) {

            window.location.href =
                `/payment-success?order_id=${data.orderID}`;

        }
        else {

            alert("Payment failed.");

        }

    },

    // =====================================
    // User Cancelled
    // =====================================

    onCancel: function () {

        alert("Payment cancelled.");

    },

    // =====================================
    // Error
    // =====================================

    onError: function (err) {

        console.error(err);

        alert("PayPal payment failed.");

    }

}).render("#paypal-button-container");