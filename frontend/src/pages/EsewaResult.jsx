import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { apiFetch } from "../api";

const CHECKOUT_CTX_KEY = "checkout_context";
const BUY_NOW_KEY = "buy_now_item";
const CART_KEY = "cart_items";

function safeParse(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function cleanupAfterEsewaSuccess() {
  const ctx = safeParse(sessionStorage.getItem(CHECKOUT_CTX_KEY));

  if (ctx?.mode === "BUY_NOW") {
    localStorage.removeItem(BUY_NOW_KEY);
    window.dispatchEvent(new Event("buy_now:updated"));
  } else if (ctx?.mode === "CART") {
    localStorage.removeItem(CART_KEY);
    window.dispatchEvent(new Event("cart:updated"));
  }

  sessionStorage.removeItem(CHECKOUT_CTX_KEY);
}

export default function EsewaResult() {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  const orderId = params.get("order_id");
  const initialPaymentStatus = params.get("payment_status") || "";
  const initialEsewaStatus = params.get("esewa_status") || "";
  const refId = params.get("ref_id") || "";

  const initialStatus = useMemo(() => {
    return String(initialEsewaStatus || initialPaymentStatus || "UNKNOWN").toUpperCase();
  }, [initialEsewaStatus, initialPaymentStatus]);

  const [status, setStatus] = useState(initialStatus);
  const [paymentStatus, setPaymentStatus] = useState(
    String(initialPaymentStatus || "UNKNOWN").toUpperCase()
  );
  const [loading, setLoading] = useState(
    ["PENDING", "AMBIGUOUS"].includes(initialStatus)
  );
  const [error, setError] = useState("");

  useEffect(() => {
    if (status === "COMPLETE") {
      cleanupAfterEsewaSuccess();
    }
  }, [status]);

  useEffect(() => {
    if (!orderId) {
      setLoading(false);
      return;
    }

    if (!["PENDING", "AMBIGUOUS"].includes(status)) {
      setLoading(false);
      return;
    }

    let alive = true;
    let timer = null;

    async function runPoll() {
      try {
        const res = await apiFetch(`/payments/esewa/poll/${orderId}`);
        if (!alive) return;

        const nextEsewaStatus = String(res?.status || "UNKNOWN").toUpperCase();
        const nextPaymentStatus = String(res?.payment_status || "UNKNOWN").toUpperCase();

        setStatus(nextEsewaStatus);
        setPaymentStatus(nextPaymentStatus);

        if (!["PENDING", "AMBIGUOUS"].includes(nextEsewaStatus)) {
          setLoading(false);
          if (timer) clearInterval(timer);
        }
      } catch (e) {
        if (!alive) return;
        setError(e?.message || "Failed to verify payment status");
        setLoading(false);
      }
    }

    runPoll();
    timer = setInterval(runPoll, 3000);

    return () => {
      alive = false;
      if (timer) clearInterval(timer);
    };
  }, [orderId, status]);

  function titleText() {
    if (loading) return "Verifying Payment";
    if (status === "COMPLETE") return "Payment Successful";
    if (status === "CANCELED") return "Payment Canceled";
    if (status === "FAILED") return "Payment Failed";
    if (status === "NOT_FOUND") return "Payment Not Found";
    if (status === "FULL_REFUND") return "Payment Refunded";
    if (status === "PARTIAL_REFUND") return "Payment Partially Refunded";
    return "Payment Result";
  }

  function messageText() {
    if (!orderId) return "Order ID is missing from the callback URL.";
    if (loading) return "We are verifying your eSewa payment. Please wait a moment.";
    if (status === "COMPLETE") return "Your payment has been completed successfully.";
    if (status === "CANCELED") return "Your payment was canceled.";
    if (status === "FAILED") return "Your payment could not be completed.";
    if (status === "NOT_FOUND") return "The payment record could not be found.";
    if (status === "FULL_REFUND") return "This payment was fully refunded.";
    if (status === "PARTIAL_REFUND") return "This payment was partially refunded.";
    return `Current status: ${status}`;
  }

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: 20 }}>
      <h1>{titleText()}</h1>

      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 12,
          padding: 20,
          background: "#fff",
        }}
      >
        <p><strong>Order ID:</strong> {orderId || "-"}</p>
        <p><strong>eSewa Status:</strong> {status}</p>
        <p><strong>Payment Status:</strong> {paymentStatus}</p>
        {refId ? <p><strong>Reference ID:</strong> {refId}</p> : null}
        <p>{messageText()}</p>
        {error ? <p style={{ color: "red" }}>{error}</p> : null}
      </div>

      <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
        <Link to="/products">Continue Shopping</Link>

        {status !== "COMPLETE" ? (
          <button type="button" onClick={() => navigate("/payment")}>
            Try Again
          </button>
        ) : null}
      </div>
    </div>
  );
}