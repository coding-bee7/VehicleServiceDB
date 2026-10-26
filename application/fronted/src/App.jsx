import { useEffect, useRef, useState } from "react";
import CarScene from "./CarScene";
import "./App.css";
import { api } from "./services/api";

const services = [
  {
    number: "01",
    title: "Routine Maintenance",
    description: "Thoughtful care that keeps every journey running smoothly.",
    icon: "✳",
  },
  {
    number: "02",
    title: "Engine & Diagnostics",
    description: "Precision diagnostics for the details you cannot see.",
    icon: "⌁",
  },
  {
    number: "03",
    title: "Premium Detailing",
    description: "Restore the finish. Refine every surface.",
    icon: "◇",
  },
];

const initialBooking = {
  vehicle_id: "",
  serviceType: "Routine Maintenance",
  date: "",
  time: "",
  description: "",
};

function App() {
  const [page, setPage] = useState("home");
  const [authMode, setAuthMode] = useState("login");
  const [menuOpen, setMenuOpen] = useState(false);
  const [cursor, setCursor] = useState({ x: -30, y: -30 });
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem("autodb-user") || "null");
    } catch {
      return null;
    }
  });
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [nextAppointment, setNextAppointment] = useState(null);
  const [nextAppointmentError, setNextAppointmentError] = useState("");
  const [appointments, setAppointments] = useState([]);
  const [mechanicServices, setMechanicServices] = useState([]);
  const [mechanicServicesError, setMechanicServicesError] = useState("");
  const [mechanicServicesLoading, setMechanicServicesLoading] = useState(false);
  const [completingServiceId, setCompletingServiceId] = useState(null);
  const [adminAppointments, setAdminAppointments] = useState([]);
  const [adminAppointmentsError, setAdminAppointmentsError] = useState("");
  const [adminMechanics, setAdminMechanics] = useState([]);
  const [adminMechanicsError, setAdminMechanicsError] = useState("");
  const [updatingAppointmentId, setUpdatingAppointmentId] = useState(null);
  const [appointmentUpdateError, setAppointmentUpdateError] = useState("");
  const [appointmentUpdateNotice, setAppointmentUpdateNotice] = useState("");
  const [booking, setBooking] = useState(initialBooking);
  const [vehicles, setVehicles] = useState([]);
  const [vehiclesError, setVehiclesError] = useState("");

  const [invoices, setInvoices] = useState([]);
  const [invoicesError, setInvoicesError] = useState("");
  const [invoiceLoading, setInvoiceLoading] = useState(false);
  const [payments, setPayments] = useState([]);
  const [paymentsError, setPaymentsError] = useState("");
  const [paymentsLoading, setPaymentsLoading] = useState(false);
  // Customer invoice state
  const [customerInvoices, setCustomerInvoices] = useState([]);
  const [customerInvoicesLoading, setCustomerInvoicesLoading] = useState(false);
  const [customerInvoicesError, setCustomerInvoicesError] = useState("");
  const [customerInvoiceDetails, setCustomerInvoiceDetails] = useState(null);
  const [customerInvoiceDetailsLoading, setCustomerInvoiceDetailsLoading] =
    useState(false);
  const [customerInvoiceDetailsError, setCustomerInvoiceDetailsError] =
    useState("");
  const [showCustomerInvoiceDetails, setShowCustomerInvoiceDetails] =
    useState(false);

  const clearCustomerInvoiceState = () => {
  setCustomerInvoices([]);
  setCustomerInvoicesError("");
  setCustomerInvoicesLoading(false);
  setCustomerInvoiceDetails(null);
  setCustomerInvoiceDetailsError("");
  setCustomerInvoiceDetailsLoading(false);
  setShowCustomerInvoiceDetails(false);
};

  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("Cash");
  const [paymentSaving, setPaymentSaving] = useState(false);
  const [paymentError, setPaymentError] = useState("");
  const [paymentNotice, setPaymentNotice] = useState("");
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [invoiceDetails, setInvoiceDetails] = useState(null);
  const [invoiceDetailsLoading, setInvoiceDetailsLoading] = useState(false);
  const [invoiceDetailsError, setInvoiceDetailsError] = useState("");
  const [showInvoiceDetails, setShowInvoiceDetails] = useState(false);

  const [vehicleForm, setVehicleForm] = useState({
    registrationNo: "",
    brand: "",
    model: "",
    manufactureYear: "",
    fuelType: "",
  });
  const [vehicleSaving, setVehicleSaving] = useState(false);
  const [vehicleNotice, setVehicleNotice] = useState("");
  const [vehicleFormError, setVehicleFormError] = useState("");

  const [staffSaving, setStaffSaving] = useState(false);
  const [staffNotice, setStaffNotice] = useState("");
  const [staffError, setStaffError] = useState("");

  const cursorRef = useRef(null);

  const navigate = (nextPage) => {
    setPage(nextPage);
    setMenuOpen(false);
    setNotice("");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const scrollTo = (id) => {
    if (page !== "home") setPage("home");
    window.setTimeout(
      () => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" }),
      page === "home" ? 0 : 60
    );
    setMenuOpen(false);
  };

  useEffect(() => {
    const finePointer = window.matchMedia("(pointer: fine)").matches;
    if (!finePointer) return;
    const moveCursor = (event) => {
      if (cursorRef.current) {
        cursorRef.current.style.left = `${event.clientX}px`;
        cursorRef.current.style.top = `${event.clientY}px`;
      }
    };
    window.addEventListener("pointermove", moveCursor);
    return () => window.removeEventListener("pointermove", moveCursor);
  }, []);

  useEffect(() => {
    if (!user || !["customer", "admin"].includes(user.role)) return;
    let active = true;
    const load = async () => {
      try {
        const result =
          user.role === "admin"
            ? await api.adminDashboard()
            : await api.customerDashboard();
        if (active) setDashboard(result);
      } catch (err) {
        if (active) setDashboard({ __error: err.message });
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [user]);

  useEffect(() => {
    if (!user || user.role !== "admin" || page !== "admin") return;

    let active = true;

    api
      .adminAppointments()
      .then((result) => {
        if (!active) return;

        const list = Array.isArray(result)
          ? result
          : result?.appointments || [];

        setAdminAppointments(list);
        setAdminAppointmentsError("");
      })
      .catch((err) => {
        if (!active) return;

        setAdminAppointments([]);
        setAdminAppointmentsError(
          err.message || "Could not load appointment requests."
        );
      });

    return () => {
      active = false;
    };
  }, [user, page]);

  
useEffect(() => {
  if (!user || user.role !== "admin" || page !== "admin") return;

  let active = true;

  api
    .adminMechanics()
    .then((result) => {
      if (!active) return;

      const list = Array.isArray(result)
        ? result
        : result?.mechanics || [];

      setAdminMechanics(list);
      setAdminMechanicsError("");
    })
    .catch((err) => {
      if (!active) return;

      setAdminMechanics([]);
      setAdminMechanicsError(
        err.message || "Could not load the mechanics list."
      );
    });

  return () => {
    active = false;
  };
}, [user, page]);


  useEffect(() => {
    if (!user || user.role !== "mechanic" || page !== "mechanic") return;

    let active = true;
    setMechanicServicesLoading(true);

    api
      .mechanicServices()
      .then((result) => {
        if (!active) return;
        const list = Array.isArray(result) ? result : result?.value || [];
        setMechanicServices(list);
        setMechanicServicesError("");
      })
      .catch((err) => {
        if (!active) return;
        setMechanicServices([]);
        setMechanicServicesError(
          err.message || "Could not load assigned services."
        );
      })
      .finally(() => {
        if (active) setMechanicServicesLoading(false);
      });

    return () => {
      active = false;
    };
  }, [user, page]);

  useEffect(() => {
    if (!user || user.role !== "customer") {
      setNextAppointment(null);
      setNextAppointmentError("");
      return;
    }

    let active = true;

    api
      .nextAppointment()
      .then((result) => {
        if (!active) return;
        setNextAppointment(result || null);
        setNextAppointmentError("");
      })
      .catch((err) => {
        if (!active) return;
        setNextAppointment(null);
        setNextAppointmentError(
          err.message || "Could not load your next appointment."
        );
      });

    return () => {
      active = false;
    };
  }, [user]);

  useEffect(() => {
    if (!user || user.role !== "customer" || page !== "my-services") return;
    let active = true;
    api
      .myServices()
      .then((result) => {
        if (active)
          setAppointments(
            Array.isArray(result) ? result : result?.appointments || []
          );
      })
      .catch((err) => {
        if (active) setError(err.message);
      });
    return () => {
      active = false;
    };
  }, [user, page]);

  useEffect(() => {
    if (!user || user.role !== "customer" || page !== "book") return;

    let active = true;

    api
      .myVehicles()
      .then((result) => {
        if (!active) return;

        const list = Array.isArray(result) ? result : result?.vehicles || [];
        setVehicles(list);
        setVehiclesError("");

        setBooking((current) => ({
          ...current,
          vehicle_id:
            current.vehicle_id ||
            (list.length ? String(list[0].VehicleID) : ""),
        }));
      })
      .catch((err) => {
        if (active)
          setVehiclesError(err.message || "Could not load your vehicles.");
      });

    return () => {
      active = false;
    };
  }, [user, page]);

  useEffect(() => {
    if (!user || user.role !== "customer" || page !== "my-vehicles") {
      return;
    }

    let active = true;

    api
      .myVehicles()
      .then((result) => {
        if (!active) return;

        const list = Array.isArray(result)
          ? result
          : result?.vehicles || result?.value || [];

        setVehicles(list);
        setVehiclesError("");
      })
      .catch((err) => {
        if (!active) return;

        setVehiclesError(err.message || "Could not load your vehicles.");
      });

    return () => {
      active = false;
    };
  }, [user, page]);

  useEffect(() => {
  if (!user || user.role !== "customer" || page !== "my-invoices") {
    return;
  }

  let active = true;

  setCustomerInvoicesLoading(true);
  setCustomerInvoicesError("");

  api
    .myInvoices()
    .then((result) => {
      if (!active) return;

      const list = Array.isArray(result)
        ? result
        : result?.invoices || [];

      setCustomerInvoices(list);
      setCustomerInvoicesError("");
    })
    .catch((err) => {
      if (!active) return;

      setCustomerInvoices([]);
      setCustomerInvoicesError(
        err.message || "Could not load your invoices."
      );
    })
    .finally(() => {
      if (active) setCustomerInvoicesLoading(false);
    });

  return () => {
    active = false;
  };
}, [user, page]);

  useEffect(() => {
    if (
      !user ||
      user.role !== "admin" ||
      page !== "payments"
    ) {
      return;
    }

    let active = true;
    setInvoiceLoading(true);
    setInvoicesError("");

    api
      .invoices()
      .then((result) => {
        if (!active) return;

        const list = Array.isArray(result) ? result : [];
        setInvoices(list);

        setSelectedInvoiceId((current) => {
          if (list.some((item) => String(item.InvoiceID) === current)) {
            return current;
          }

          const outstanding = list.find(
            (item) => Number(item.OutstandingBalance) > 0
          );

          return outstanding ? String(outstanding.InvoiceID) : "";
        });

        setInvoicesError("");
      })
      .catch((err) => {
        if (active) {
          setInvoicesError(err.message || "Could not load invoices.");
        }
      })
      .finally(() => {
        if (active) setInvoiceLoading(false);
      });

    return () => {
      active = false;
    };
  }, [user, page]);

  useEffect(() => {
    if (
      !user ||
      user.role !== "admin" ||
      page !== "payments"
    ) {
      return;
    }

    let active = true;
    setPaymentsLoading(true);
    setPaymentsError("");

    api
      .payments()
      .then((result) => {
        if (!active) return;
        setPayments(Array.isArray(result) ? result : []);
      })
      .catch((err) => {
        if (active) {
          setPaymentsError(err.message || "Could not load payment history.");
        }
      })
      .finally(() => {
        if (active) setPaymentsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [user, page]);

  const handleViewInvoice = async (invoiceId) => {
    setShowInvoiceDetails(true);
    setInvoiceDetails(null);
    setInvoiceDetailsError("");
    setInvoiceDetailsLoading(true);

    try {
      const result = await api.invoiceDetails(invoiceId);
      setInvoiceDetails(result);
    } catch (err) {
      setInvoiceDetailsError(err.message || "Could not load invoice details.");
    } finally {
      setInvoiceDetailsLoading(false);
    }
  };


  
const handleViewCustomerInvoice = async (invoiceId) => {
  const requestedUser = user;

  setShowCustomerInvoiceDetails(true);
  setCustomerInvoiceDetails(null);
  setCustomerInvoiceDetailsError("");
  setCustomerInvoiceDetailsLoading(true);

  try {
    const result = await api.myInvoiceDetails(invoiceId);

    // Ignore the response if the account changed while loading.
    if (user !== requestedUser) return;

    setCustomerInvoiceDetails(result);
  } catch (err) {
    if (user !== requestedUser) return;

    setCustomerInvoiceDetailsError(
      err.message || "Could not load invoice details."
    );
  } finally {
    if (user === requestedUser) {
      setCustomerInvoiceDetailsLoading(false);
    }
  }
};


  const handleRecordPayment = async (event) => {
    event.preventDefault();

    if (!selectedInvoiceId) {
      setPaymentError("Please select an invoice.");
      return;
    }

    if (!paymentAmount || Number(paymentAmount) <= 0) {
      setPaymentError("Enter a payment amount greater than zero.");
      return;
    }

    setPaymentSaving(true);
    setPaymentError("");
    setPaymentNotice("");

    try {
      const result = await api.recordPayment(selectedInvoiceId, {
        amount: paymentAmount,
        paymentMethod,
      });

      setPaymentNotice(result.message || "Payment recorded successfully.");
      setPaymentAmount("");

      // Refresh invoice balances and payment statuses.
      const updatedInvoices = await api.invoices();
      setInvoices(Array.isArray(updatedInvoices) ? updatedInvoices : []);
    } catch (err) {
      setPaymentError(err.message || "Could not record payment.");
    } finally {
      setPaymentSaving(false);
    }
  };

  const handleAuth = async (event, form) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");

    try {
      if (authMode === "register") {
        await api.register({
          name: form.name,
          phone: form.phone,
          email: form.email,
          password: form.password,
        });

        setAuthMode("login");
        setNotice("Account created successfully. Please sign in.");
        return;
      }

      const result = await api.login({
        email: form.email,
        password: form.password,
      });

      const token = result?.access_token || result?.token;
      const rawAccount = result?.user || result?.account;

      if (!rawAccount) {
        throw new Error(
          "Login succeeded, but the API response did not include a user object."
        );
      }

      if (!token) {
        throw new Error("The login response did not include an access token.");
      }

      const account = {
        ...rawAccount,
        name: rawAccount.name || rawAccount.Name || "",
        role: String(rawAccount.role || rawAccount.Role || "").toLowerCase(),
      };

      if (!["customer", "admin", "mechanic"].includes(account.role)) {
        throw new Error("The account has an unsupported role.");
      }

      clearCustomerInvoiceState();

      setInvoices([]);
      setInvoicesError("");
      setInvoiceDetails(null);
      setInvoiceDetailsError("");
      setShowInvoiceDetails(false);

      sessionStorage.setItem("autodb-token", token);
      sessionStorage.setItem("autodb-user", JSON.stringify(account));

      setUser(account);

      if (account.role === "admin") {
        navigate("admin");
      } else if (account.role === "mechanic") {
        navigate("mechanic");
      } else {
        navigate("dashboard");
      }
    } catch (err) {
      setError(err.message || "Unable to authenticate. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleBooking = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const result = await api.createAppointment(booking);
      setNotice(result?.message || "Your booking request was submitted.");
      setBooking(initialBooking);
    } catch (err) {
      setError(err.message || "Could not submit your booking.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVehicle = async (event) => {
    event.preventDefault();
    setVehicleSaving(true);
    setVehicleNotice("");
    setVehicleFormError("");
    setVehiclesError("");

    try {
      await api.createVehicle(vehicleForm);

      const result = await api.myVehicles();
      const list = Array.isArray(result)
        ? result
        : result?.vehicles || result?.value || [];

      setVehicles(list);
      setVehicleForm({
        registrationNo: "",
        brand: "",
        model: "",
        manufactureYear: "",
        fuelType: "",
      });
      setVehicleNotice("Vehicle registered successfully.");
    } catch (err) {
      setVehicleFormError(err.message || "Could not register vehicle.");
    } finally {
      setVehicleSaving(false);
    }
  };

  const handleAppointmentStatusUpdate = async (appointmentId, status) => {
    setUpdatingAppointmentId(appointmentId);
    setAppointmentUpdateError("");
    setAppointmentUpdateNotice("");

    try {
      await api.updateAppointment(appointmentId, { Status: status });

      const result = await api.adminAppointments();
      const list = Array.isArray(result) ? result : result?.appointments || [];

      setAdminAppointments(list);
      setAppointmentUpdateNotice(
        `Appointment #${appointmentId} updated successfully.`
      );
    } catch (err) {
      setAppointmentUpdateError(
        err.message || "Could not update the appointment status."
      );
    } finally {
      setUpdatingAppointmentId(null);
    }
  };


  
const handleAssignMechanic = async (appointmentId, mechanicId) => {
  setUpdatingAppointmentId(appointmentId);
  setAppointmentUpdateError("");
  setAppointmentUpdateNotice("");

  try {
    const result = await api.assignMechanic(
      appointmentId,
      mechanicId
    );

    const updatedAppointments = await api.adminAppointments();
    const list = Array.isArray(updatedAppointments)
      ? updatedAppointments
      : updatedAppointments?.appointments || [];

    setAdminAppointments(list);

    setAppointmentUpdateNotice(
      result?.message ||
        `Mechanic assigned to appointment #${appointmentId}.`
    );
  } catch (err) {
    setAppointmentUpdateError(
      err.message || "Could not assign the mechanic."
    );
  } finally {
    setUpdatingAppointmentId(null);
  }
};


  const handleCreateStaff = async (form) => {
  setStaffSaving(true);
  setStaffNotice("");
  setStaffError("");

  try {
    const result = await api.createStaff(form);

    setStaffNotice(
      result.message || "Mechanic account created successfully."
    );

    return true;
  } catch (err) {
    setStaffError(err.message || "Could not create mechanic account.");
    return false;
  } finally {
    setStaffSaving(false);
  }
};

  const handleStartService = async (serviceId) => {
    setCompletingServiceId(serviceId);
    setMechanicServicesError("");

    try {
      await api.startService(serviceId);

      const result = await api.mechanicServices();
      const list = Array.isArray(result) ? result : result?.value || [];

      setMechanicServices(list);
      setNotice(`Service #${serviceId} started successfully.`);
    } catch (err) {
      setMechanicServicesError(err.message || "Could not start this service.");
    } finally {
      setCompletingServiceId(null);
    }
  };

  const handleCompleteService = async (serviceId) => {
    setCompletingServiceId(serviceId);
    setMechanicServicesError("");

    try {
      await api.completeService(serviceId);

      const result = await api.mechanicServices();
      const list = Array.isArray(result) ? result : result?.value || [];

      setMechanicServices(list);
      setNotice(`Service #${serviceId} completed successfully.`);
    } catch (err) {
      setMechanicServicesError(
        err.message || "Could not complete this service."
      );
    } finally {
      setCompletingServiceId(null);
    }
  };

  const logout = () => {
    clearCustomerInvoiceState();

  sessionStorage.removeItem("autodb-token");
  sessionStorage.removeItem("autodb-user");

  setUser(null);
  setDashboard(null);
  setAppointments([]);
  setInvoices([]);
  setInvoicesError("");
  setInvoiceDetails(null);
  setInvoiceDetailsError("");
  setShowInvoiceDetails(false);

  navigate("home");
  };

  const requireCustomer = () => {
    if (!user) {
      setAuthMode("login");
      navigate("auth");
      return false;
    }
    if (user.role !== "customer") {
      navigate("admin");
      return false;
    }
    return true;
  };

  if (page === "home")
    return (
      <main className="autodb-home">
        <nav className="navbar">
          <a
            className="brand"
            href="#home"
            onClick={(e) => {
              e.preventDefault();
              scrollTo("home");
            }}
            aria-label="AutoDB home"
          >
            AUTO<span>DB</span>
            <small>THE ART OF AUTOMOTIVE CARE</small>
          </a>
          <button
            className="menu-toggle"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle navigation"
            aria-expanded={menuOpen}
          >
            {menuOpen ? "✕" : "☰"}
          </button>
          <div className={`nav-links ${menuOpen ? "nav-links-open" : ""}`}>
            <button onClick={() => scrollTo("services")}>OUR SERVICES</button>
            <button onClick={() => scrollTo("about")}>OUR PHILOSOPHY</button>
            <button
              className="nav-cta"
              onClick={() => {
                if (user) navigate("book");
                else {
                  setAuthMode("login");
                  navigate("auth");
                }
              }}
            >
              BOOK A SERVICE <span>↗</span>
            </button>
            {user ? (
              <button
                onClick={() =>
                  navigate(user.role === "admin" ? "admin" : "dashboard")
                }
              >
                MY ACCOUNT
              </button>
            ) : (
              <button
                onClick={() => {
                  setAuthMode("login");
                  navigate("auth");
                }}
              >
                SIGN IN
              </button>
            )}
          </div>
        </nav>

        <section className="hero" id="home">
          <div className="hero-image" aria-hidden="true" />
          <div className="hero-overlay" />
          <CarScene />
          <div className="hero-content">
            <p className="eyebrow hero-eyebrow">
              <span /> A HIGHER STANDARD OF CARE
            </p>
            <h1>
              Driven by
              <br />
              <em>excellence.</em>
            </h1>
            <p className="hero-description">
              Exceptional vehicles deserve exceptional care. Discover a more
              considered approach to vehicle servicing and maintenance.
            </p>
            <div className="hero-actions">
              <button
                className="button button-light"
                onClick={() => scrollTo("services")}
              >
                EXPLORE OUR SERVICES <span>↗</span>
              </button>
              <button className="text-link" onClick={() => scrollTo("about")}>
                DISCOVER AUTODB <span>↓</span>
              </button>
            </div>
          </div>
          <div className="hero-caption">
            <span>CRAFTED FOR THE JOURNEY</span>
            <span>01 / 03</span>
          </div>
          <div className="hero-side-note">PRECISION · CARE · CONFIDENCE</div>
        </section>

        <section className="intro section-pad" id="about">
          <div className="intro-label">
            <span className="section-index">01 — THE AUTODB APPROACH</span>
            <span className="little-line" />
          </div>
          <div className="intro-copy">
            <h2>
              More than maintenance.
              <br />
              <em>A standard of its own.</em>
            </h2>
            <div className="intro-bottom">
              <p>
                Your vehicle is more than a machine. It is engineering,
                craftsmanship and freedom in motion. We bring a considered,
                detail-first approach to keeping it at its best.
              </p>
              <button
                className="round-link"
                onClick={() => scrollTo("services")}
                aria-label="Explore services"
              >
                ↘
              </button>
            </div>
          </div>
          <div className="intro-watermark" aria-hidden="true">
            A.
          </div>
        </section>

        <section className="services section-pad" id="services">
          <div className="section-heading">
            <div>
              <span className="section-index">02 — WHAT WE DO</span>
              <h2>
                Care, without
                <br />
                <em>compromise.</em>
              </h2>
            </div>
            <p>
              The right expertise. The right attention. A seamless experience
              from booking to handover.
            </p>
          </div>
          <div className="service-grid">
            {services.map((service) => (
              <article className="service-card" key={service.number}>
                <div className="service-card-top">
                  <span>{service.number}</span>
                  <span className="service-icon">{service.icon}</span>
                </div>
                <div>
                  <h3>{service.title}</h3>
                  <p>{service.description}</p>
                </div>
                <button
                  className="service-arrow"
                  onClick={() => {
                    if (user) navigate("book");
                    else {
                      setAuthMode("login");
                      navigate("auth");
                    }
                  }}
                  aria-label={`Book ${service.title}`}
                >
                  ↗
                </button>
              </article>
            ))}
          </div>
          <div className="services-cta">
            <p>Ready to give your vehicle the attention it deserves?</p>
            <button
              className="button button-dark"
              onClick={() => {
                if (user) navigate("book");
                else {
                  setAuthMode("login");
                  navigate("auth");
                }
              }}
            >
              BOOK A SERVICE <span>↗</span>
            </button>
          </div>
        </section>

        <section className="quote-section" id="contact">
          <div className="quote-mark">“</div>
          <p>
            Great journeys begin with
            <br />
            <em>exceptional care.</em>
          </p>
          <span>YOUR VEHICLE. OUR ATTENTION.</span>
          <button
            className="button button-dark"
            onClick={() => {
              if (user) navigate("book");
              else {
                setAuthMode("login");
                navigate("auth");
              }
            }}
          >
            ENQUIRE WITH AUTODB <span>↗</span>
          </button>
        </section>
        <Footer scrollTo={scrollTo} navigate={navigate} />
        <div className="custom-cursor" ref={cursorRef} aria-hidden="true">
          <span />
        </div>
      </main>
    );

  return (
    <main className="app-page">
      <AppNavbar
        user={user}
        navigate={navigate}
        logout={logout}
        menuOpen={menuOpen}
        setMenuOpen={setMenuOpen}
      />
      <div className="page-wrap">
        {page === "auth" && (
          <AuthPage
            mode={authMode}
            setMode={setAuthMode}
            onSubmit={handleAuth}
            loading={loading}
            error={error}
            notice={notice}
          />
        )}
        {page === "dashboard" && (
          <CustomerDashboard
            user={user}
            data={dashboard}
            nextAppointment={nextAppointment}
            nextAppointmentError={nextAppointmentError}
            navigate={navigate}
          />
        )}
        {page === "book" && (
          <BookService
            user={user}
            booking={booking}
            setBooking={setBooking}
            onSubmit={handleBooking}
            loading={loading}
            error={error}
            notice={notice}
            requireCustomer={requireCustomer}
            vehicles={vehicles}
            vehiclesError={vehiclesError}
          />
        )}
        {page === "my-services" && (
          <MyServices
            appointments={appointments}
            error={error}
            navigate={navigate}
          />
        )}

        {page === "my-vehicles" && (
          <MyVehicles
            vehicles={vehicles}
            loading={vehicleSaving}
            error={vehiclesError}
            formError={vehicleFormError}
            notice={vehicleNotice}
            form={vehicleForm}
            setForm={setVehicleForm}
            onSubmit={handleCreateVehicle}
          />
        )}

        
{page === "my-invoices" && user?.role === "customer" && (
  <section className="dashboard-page">
    <PageHeading
      eyebrow="YOUR ACCOUNT"
      title={
        <>
          Every invoice,
          <br />
          <em>clearly accounted for.</em>
        </>
      }
      description="Review your service invoices, payment history and any outstanding balance."
    />

    {customerInvoicesError && (
      <ApiNotice text={customerInvoicesError} />
    )}

    {customerInvoicesLoading ? (
      <p className="muted">Loading your invoices...</p>
    ) : (
      <>
        <div className="stat-grid">
          <Stat
            label="TOTAL INVOICES"
            value={customerInvoices.length}
            note="Invoices linked to your vehicles"
          />
          <Stat
            label="TOTAL BILLED"
            value={`₹${customerInvoices
              .reduce(
                (sum, invoice) => sum + Number(invoice.TotalAmount || 0),
                0
              )
              .toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`}
            note="Combined invoice value"
          />
          <Stat
            label="OUTSTANDING"
            value={`₹${customerInvoices
              .reduce(
                (sum, invoice) =>
                  sum + Number(invoice.OutstandingBalance || 0),
                0
              )
              .toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`}
            note="Amount remaining to be paid"
          />
        </div>

        <div className="table-panel">
          <div className="table-title">
            <div>
              <span className="section-index">BILLING RECORDS</span>
              <h3>My service invoices</h3>
            </div>
            <span className="muted">
              {customerInvoices.length} records
            </span>
          </div>

          {customerInvoices.length === 0 ? (
            <EmptyState
              title="No invoices just yet."
              body="Your invoices will appear here when a service has been invoiced."
              action={() => navigate("my-services")}
              actionText="VIEW MY SERVICES"
            />
          ) : (
            <div className="responsive-table">
              <table>
                <thead>
                  <tr>
                    <th>INVOICE</th>
                    <th>DATE</th>
                    <th>VEHICLE</th>
                    <th>TOTAL</th>
                    <th>PAID</th>
                    <th>BALANCE</th>
                    <th>STATUS</th>
                    <th>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {customerInvoices.map((invoice) => (
                    <tr key={invoice.InvoiceID}>
                      <td>#{invoice.InvoiceID}</td>
                      <td>
                        {invoice.InvoiceDate
                          ? new Date(
                              invoice.InvoiceDate
                            ).toLocaleDateString("en-IN")
                          : "—"}
                      </td>
                      <td>
                        <strong>
                          {[invoice.Brand, invoice.Model]
                            .filter(Boolean)
                            .join(" ") || "—"}
                        </strong>
                        <br />
                        <small>{invoice.RegistrationNo || "—"}</small>
                      </td>
                      <td>
                        ₹{Number(invoice.TotalAmount || 0).toFixed(2)}
                      </td>
                      <td>
                        ₹{Number(invoice.AmountPaid || 0).toFixed(2)}
                      </td>
                      <td>
                        ₹
                        {Number(
                          invoice.OutstandingBalance || 0
                        ).toFixed(2)}
                      </td>
                      <td>
                        <StatusBadge
                          status={invoice.PaymentStatus || "Unpaid"}
                        />
                      </td>
                      <td>
                        <button
                          type="button"
                          className="button button-dark"
                          onClick={() =>
                            handleViewCustomerInvoice(invoice.InvoiceID)
                          }
                        >
                          View Invoice
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {user?.role === "customer" &&
  showCustomerInvoiceDetails &&
  customerInvoiceDetails && (
          <section className="invoice-preview-panel">
            <div className="invoice-preview-actions no-print">
              <h2>Invoice Details</h2>
              <div>
                <button
                  type="button"
                  disabled={
                    !customerInvoiceDetails ||
                    customerInvoiceDetailsLoading
                  }
                  onClick={() => window.print()}
                >
                  Print / Save as PDF
                </button>
                <button
                  type="button"
                  onClick={() => setShowCustomerInvoiceDetails(false)}
                >
                  Close
                </button>
              </div>
            </div>

            {customerInvoiceDetailsLoading && (
              <p>Loading invoice details...</p>
            )}

            {customerInvoiceDetailsError && (
              <p className="payment-error">
                {customerInvoiceDetailsError}
              </p>
            )}

            {customerInvoiceDetails &&
              !customerInvoiceDetailsLoading && (
                <div className="invoice-print-area">
                  <h1>AutoDB</h1>
                  <h2>
                    Service Invoice #{customerInvoiceDetails.InvoiceID}
                  </h2>

                  <p>
                    <strong>Invoice Date:</strong>{" "}
                    {customerInvoiceDetails.InvoiceDate
                      ? new Date(
                          customerInvoiceDetails.InvoiceDate
                        ).toLocaleDateString("en-IN")
                      : "—"}
                  </p>

                  <hr />

                  <h3>Customer Details</h3>
                  <p>
                    <strong>Name:</strong>{" "}
                    {customerInvoiceDetails.CustomerName || "—"}
                  </p>
                  <p>
                    <strong>Email:</strong>{" "}
                    {customerInvoiceDetails.CustomerEmail || "—"}
                  </p>
                  <p>
                    <strong>Phone:</strong>{" "}
                    {customerInvoiceDetails.CustomerPhone || "—"}
                  </p>
                  <p>
                    <strong>Address:</strong>{" "}
                    {customerInvoiceDetails.CustomerAddress || "—"}
                  </p>

                  <h3>Vehicle Details</h3>
                  <p>
                    <strong>Vehicle:</strong>{" "}
                    {[customerInvoiceDetails.Brand, customerInvoiceDetails.Model]
                      .filter(Boolean)
                      .join(" ") || "—"}
                  </p>
                  <p>
                    <strong>Registration:</strong>{" "}
                    {customerInvoiceDetails.RegistrationNo || "—"}
                  </p>
                  <p>
                    <strong>Manufacture Year:</strong>{" "}
                    {customerInvoiceDetails.ManufactureYear || "—"}
                  </p>
                  <p>
                    <strong>Odometer:</strong>{" "}
                    {customerInvoiceDetails.Odometer ?? "—"}
                  </p>

                  <h3>Service Details</h3>
                  <p>
                    <strong>Service ID:</strong>{" "}
                    {customerInvoiceDetails.ServiceID}
                  </p>
                  <p>
                    <strong>Service Status:</strong>{" "}
                    {customerInvoiceDetails.ServiceStatus || "—"}
                  </p>
                  <p>
                    <strong>Start Date:</strong>{" "}
                    {customerInvoiceDetails.ServiceStartDate
                      ? new Date(
                          customerInvoiceDetails.ServiceStartDate
                        ).toLocaleDateString("en-IN")
                      : "—"}
                  </p>
                  <p>
                    <strong>End Date:</strong>{" "}
                    {customerInvoiceDetails.ServiceEndDate
                      ? new Date(
                          customerInvoiceDetails.ServiceEndDate
                        ).toLocaleDateString("en-IN")
                      : "—"}
                  </p>

                  <hr />

                  <h3>Payment Summary</h3>
                  <p>
                    <strong>Invoice Total:</strong> ₹
                    {Number(
                      customerInvoiceDetails.TotalAmount || 0
                    ).toFixed(2)}
                  </p>
                  <p>
                    <strong>Amount Paid:</strong> ₹
                    {Number(
                      customerInvoiceDetails.AmountPaid || 0
                    ).toFixed(2)}
                  </p>
                  <p>
                    <strong>Outstanding Balance:</strong> ₹
                    {Number(
                      customerInvoiceDetails.OutstandingBalance || 0
                    ).toFixed(2)}
                  </p>
                  <p>
                    <strong>Payment Status:</strong>{" "}
                    {customerInvoiceDetails.PaymentStatus || "Unpaid"}
                  </p>

                  <h3>Payment History</h3>

                  {customerInvoiceDetails.Payments?.length ? (
                    <table>
                      <thead>
                        <tr>
                          <th>Payment ID</th>
                          <th>Date</th>
                          <th>Method</th>
                          <th>Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {customerInvoiceDetails.Payments.map((payment) => (
                          <tr key={payment.PaymentID}>
                            <td>{payment.PaymentID}</td>
                            <td>
                              {payment.PaymentDate
                                ? new Date(
                                    payment.PaymentDate
                                  ).toLocaleDateString("en-IN")
                                : "—"}
                            </td>
                            <td>{payment.PaymentMethod || "—"}</td>
                            <td>
                              ₹{Number(payment.Amount || 0).toFixed(2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p>No payments recorded.</p>
                  )}

                  <p className="invoice-footer">
                    Thank you for choosing AutoDB.
                  </p>
                </div>
              )}
          </section>
        )}
      </>
    )}
  </section>
)}


        
        {page === "admin" && (
          <AdminDashboard
            user={user}
            data={dashboard}
            appointments={adminAppointments}
            appointmentsError={adminAppointmentsError}
            mechanics={adminMechanics}
            mechanicsError={adminMechanicsError}
            onAssignMechanic={handleAssignMechanic}
            updatingAppointmentId={updatingAppointmentId}
            appointmentUpdateError={appointmentUpdateError}
            appointmentUpdateNotice={appointmentUpdateNotice}
            onUpdateAppointment={handleAppointmentStatusUpdate}
            navigate={navigate}
            onCreateStaff={handleCreateStaff}
            staffSaving={staffSaving}
            staffNotice={staffNotice}
            staffError={staffError}
          />
        )}

        {page === "payments" && user?.role === "admin" && (
          <main className="payments-page">
            {showInvoiceDetails && (
              <section className="invoice-preview-panel">
                <div className="invoice-preview-actions no-print">
                  <h2>Invoice Details</h2>

                  <div>
                    <button
                      type="button"
                      disabled={!invoiceDetails || invoiceDetailsLoading}
                      onClick={() => window.print()}
                    >
                      Print / Save as PDF
                    </button>

                    <button
                      type="button"
                      onClick={() => setShowInvoiceDetails(false)}
                    >
                      Close
                    </button>
                  </div>
                </div>

                {invoiceDetailsLoading && <p>Loading invoice details...</p>}

                {invoiceDetailsError && (
                  <p className="payment-error">{invoiceDetailsError}</p>
                )}

                {invoiceDetails && !invoiceDetailsLoading && (
                  <div className="invoice-print-area">
                    <h1>AutoDB</h1>
                    <h2>Service Invoice #{invoiceDetails.InvoiceID}</h2>

                    <p>
                      <strong>Invoice Date:</strong>{" "}
                      {invoiceDetails.InvoiceDate
                        ? new Date(
                            invoiceDetails.InvoiceDate
                          ).toLocaleDateString()
                        : "—"}
                    </p>

                    <hr />

                    <h3>Customer Details</h3>
                    <p>
                      <strong>Name:</strong>{" "}
                      {invoiceDetails.CustomerName || "—"}
                    </p>
                    <p>
                      <strong>Email:</strong>{" "}
                      {invoiceDetails.CustomerEmail || "—"}
                    </p>
                    <p>
                      <strong>Phone:</strong>{" "}
                      {invoiceDetails.CustomerPhone || "—"}
                    </p>
                    <p>
                      <strong>Address:</strong>{" "}
                      {invoiceDetails.CustomerAddress || "—"}
                    </p>

                    <h3>Vehicle Details</h3>
                    <p>
                      <strong>Vehicle:</strong>{" "}
                      {[invoiceDetails.Brand, invoiceDetails.Model]
                        .filter(Boolean)
                        .join(" ") || "—"}
                    </p>
                    <p>
                      <strong>Registration:</strong>{" "}
                      {invoiceDetails.RegistrationNo || "—"}
                    </p>
                    <p>
                      <strong>Year:</strong>{" "}
                      {invoiceDetails.ManufactureYear || "—"}
                    </p>
                    <p>
                      <strong>Odometer:</strong>{" "}
                      {invoiceDetails.Odometer ?? "—"}
                    </p>

                    <h3>Service Details</h3>
                    <p>
                      <strong>Service ID:</strong> {invoiceDetails.ServiceID}
                    </p>
                    <p>
                      <strong>Status:</strong>{" "}
                      {invoiceDetails.ServiceStatus || "—"}
                    </p>
                    <p>
                      <strong>Start Date:</strong>{" "}
                      {invoiceDetails.ServiceStartDate
                        ? new Date(
                            invoiceDetails.ServiceStartDate
                          ).toLocaleDateString()
                        : "—"}
                    </p>
                    <p>
                      <strong>End Date:</strong>{" "}
                      {invoiceDetails.ServiceEndDate
                        ? new Date(
                            invoiceDetails.ServiceEndDate
                          ).toLocaleDateString()
                        : "—"}
                    </p>

                    <hr />

                    <h3>Payment Summary</h3>
                    <p>
                      <strong>Invoice Total:</strong> ₹
                      {Number(invoiceDetails.TotalAmount || 0).toFixed(2)}
                    </p>
                    <p>
                      <strong>Amount Paid:</strong> ₹
                      {Number(invoiceDetails.AmountPaid || 0).toFixed(2)}
                    </p>
                    <p>
                      <strong>Outstanding Balance:</strong> ₹
                      {Number(invoiceDetails.OutstandingBalance || 0).toFixed(
                        2
                      )}
                    </p>
                    <p>
                      <strong>Payment Status:</strong>{" "}
                      {invoiceDetails.PaymentStatus || "Unpaid"}
                    </p>

                    <h3>Payment History</h3>

                    {invoiceDetails.Payments?.length ? (
                      <table>
                        <thead>
                          <tr>
                            <th>Payment ID</th>
                            <th>Date</th>
                            <th>Method</th>
                            <th>Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {invoiceDetails.Payments.map((payment) => (
                            <tr key={payment.PaymentID}>
                              <td>{payment.PaymentID}</td>
                              <td>
                                {payment.PaymentDate
                                  ? new Date(
                                      payment.PaymentDate
                                    ).toLocaleDateString()
                                  : "—"}
                              </td>
                              <td>{payment.PaymentMethod || "—"}</td>
                              <td>₹{Number(payment.Amount || 0).toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <p>No payments recorded.</p>
                    )}

                    <p className="invoice-footer">
                      Thank you for choosing AutoDB.
                    </p>
                  </div>
                )}
              </section>
            )}

            <div className="payments-header">
              <p className="eyebrow">FINANCIAL MANAGEMENT</p>
              <h1>Invoice Payments</h1>
              <p>Review outstanding invoices and record customer payments.</p>
            </div>

            {invoicesError && <p className="payment-error">{invoicesError}</p>}

            {paymentNotice && (
              <p className="payment-success">{paymentNotice}</p>
            )}

            {paymentError && <p className="payment-error">{paymentError}</p>}

            {invoiceLoading ? (
              <p>Loading invoices...</p>
            ) : (
              <div className="payments-layout">
                <section className="payments-panel">
                  <h2>Invoice Register</h2>

                  {invoices.length === 0 ? (
                    <p>No invoices found.</p>
                  ) : (
                    <div className="invoice-list">
                      {invoices.map((invoice) => (
                        <div
                          key={invoice.InvoiceID}
                          className={`invoice-item ${
                            String(invoice.InvoiceID) === selectedInvoiceId
                              ? "selected"
                              : ""
                          }`}
                        >
                          <span>
                            <strong>Invoice #{invoice.InvoiceID}</strong>
                            <small>
                              {invoice.CustomerName} · {invoice.RegistrationNo}
                            </small>
                          </span>

                          <span className="invoice-item-amount">
                            <strong>
                              ₹{Number(invoice.OutstandingBalance).toFixed(2)}
                            </strong>
                            <small>{invoice.PaymentStatus}</small>
                          </span>

                          <div className="invoice-item-actions">
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedInvoiceId(String(invoice.InvoiceID));
                                setPaymentError("");
                                setPaymentNotice("");
                                setPaymentAmount("");
                              }}
                            >
                              Select
                            </button>

                            <button
                              type="button"
                              onClick={() =>
                                handleViewInvoice(invoice.InvoiceID)
                              }
                            >
                              View Invoice
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>

                <section className="payments-panel">
                  <h2>Record Payment</h2>

                  {(() => {
                    const selectedInvoice = invoices.find(
                      (invoice) =>
                        String(invoice.InvoiceID) === selectedInvoiceId
                    );

                    if (!selectedInvoice) {
                      return <p>Select an invoice to continue.</p>;
                    }

                    const outstanding = Number(
                      selectedInvoice.OutstandingBalance
                    );

                    return (
                      <>
                        <div className="payment-summary">
                          <p>
                            Invoice{" "}
                            <strong>#{selectedInvoice.InvoiceID}</strong>
                          </p>
                          <p>
                            Customer{" "}
                            <strong>{selectedInvoice.CustomerName}</strong>
                          </p>
                          <p>
                            Total{" "}
                            <strong>
                              ₹{Number(selectedInvoice.TotalAmount).toFixed(2)}
                            </strong>
                          </p>
                          <p>
                            Paid{" "}
                            <strong>
                              ₹{Number(selectedInvoice.AmountPaid).toFixed(2)}
                            </strong>
                          </p>
                          <p>
                            Outstanding{" "}
                            <strong>₹{outstanding.toFixed(2)}</strong>
                          </p>
                        </div>

                        {outstanding > 0 ? (
                          <form onSubmit={handleRecordPayment}>
                            <label htmlFor="payment-amount">
                              Payment amount (₹)
                            </label>
                            <input
                              id="payment-amount"
                              type="number"
                              min="0.01"
                              max={outstanding.toFixed(2)}
                              step="0.01"
                              value={paymentAmount}
                              onChange={(event) =>
                                setPaymentAmount(event.target.value)
                              }
                              placeholder="Enter amount"
                              required
                            />

                            <label htmlFor="payment-method">
                              Payment method
                            </label>
                            <select
                              id="payment-method"
                              value={paymentMethod}
                              onChange={(event) =>
                                setPaymentMethod(event.target.value)
                              }
                            >
                              <option value="Cash">Cash</option>
                              <option value="UPI">UPI</option>
                              <option value="Card">Card</option>
                              <option value="Bank Transfer">
                                Bank Transfer
                              </option>
                            </select>

                            <button type="submit" disabled={paymentSaving}>
                              {paymentSaving
                                ? "Recording..."
                                : "Record Payment"}
                            </button>
                          </form>
                        ) : (
                          <p>This invoice is fully paid.</p>
                        )}
                      </>
                    );
                  })()}
                </section>
              </div>
            )}
            <section className="payments-panel payment-history-panel">
              <h2>Payment History</h2>
              <p className="muted">
                Review recorded transactions and the staff members who processed
                them.
              </p>

              {paymentsError && (
                <p className="payment-error">{paymentsError}</p>
              )}

              {paymentsLoading ? (
                <p>Loading payment history...</p>
              ) : payments.length === 0 ? (
                <p>No payment transactions found.</p>
              ) : (
                <div className="responsive-table">
                  <table>
                    <thead>
                      <tr>
                        <th>PAYMENT</th>
                        <th>INVOICE</th>
                        <th>CUSTOMER / VEHICLE</th>
                        <th>AMOUNT</th>
                        <th>METHOD</th>
                        <th>RECORDED BY</th>
                        <th>DATE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payments.map((payment) => (
                        <tr key={payment.PaymentID}>
                          <td>#{payment.PaymentID}</td>
                          <td>#{payment.InvoiceID}</td>
                          <td>
                            <strong>{payment.CustomerName}</strong>
                            <br />
                            <small>{payment.RegistrationNo}</small>
                          </td>
                          <td>
                            ₹
                            {Number(payment.Amount).toLocaleString("en-IN", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </td>
                          <td>{payment.PaymentMethod}</td>
                          <td>{payment.RecordedByName}</td>
                          <td>
                            {payment.PaymentDate
                              ? new Date(payment.PaymentDate).toLocaleString(
                                  "en-IN"
                                )
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </main>
        )}
        {page === "mechanic" && (
          <MechanicDashboard
            user={user}
            services={mechanicServices}
            loading={mechanicServicesLoading}
            error={mechanicServicesError}
            notice={notice}
            completingServiceId={completingServiceId}
            onStart={handleStartService}
            onComplete={handleCompleteService}
            onRefresh={() => {
              setPage("home");
              window.setTimeout(() => setPage("mechanic"), 0);
            }}
          />
        )}
      </div>
      <Footer navigate={navigate} scrollTo={scrollTo} />
      <div className="custom-cursor" ref={cursorRef} aria-hidden="true">
        <span />
      </div>
    </main>
  );
}

function AppNavbar({ user, navigate, logout, menuOpen, setMenuOpen }) {
  return (
    <nav className="app-navbar">
      <button className="brand app-brand" onClick={() => navigate("home")}>
        AUTO<span>DB</span>
        <small>THE ART OF AUTOMOTIVE CARE</small>
      </button>
      <button
        className="menu-toggle app-menu-toggle"
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Toggle navigation"
      >
        {menuOpen ? "✕" : "☰"}
      </button>
      <div className={`app-nav-links ${menuOpen ? "app-nav-links-open" : ""}`}>
        <button onClick={() => navigate("home")}>HOME</button>
        {user?.role === "customer" && (
          <>
            <button onClick={() => navigate("dashboard")}>DASHBOARD</button>
            <button onClick={() => navigate("my-services")}>MY SERVICES</button>
            <button onClick={() => navigate("my-vehicles")}>MY VEHICLES</button>
            <button onClick={() => navigate("my-invoices")}>MY INVOICES</button>
            <button className="nav-cta" onClick={() => navigate("book")}>
              BOOK A SERVICE ↗
            </button>
          </>
        )}

        {user?.role === "admin" && (
          <>
            <button onClick={() => navigate("admin")}>ADMIN OVERVIEW</button>
            <button onClick={() => navigate("payments")}>PAYMENTS</button>
          </>
        )}

        {user ? (
          <button onClick={logout}>SIGN OUT</button>
        ) : (
          <button onClick={() => navigate("auth")}>SIGN IN</button>
        )}
      </div>
    </nav>
  );
}

function AuthPage({ mode, setMode, onSubmit, loading, error, notice }) {
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [localError, setLocalError] = useState("");
  const submit = (event) => {
    if (mode === "register" && form.password !== form.confirmPassword) {
      event.preventDefault();
      setLocalError("Your passwords do not match.");
      return;
    }
    setLocalError("");
    onSubmit(event, form);
  };
  return (
    <section className="auth-layout">
      <div className="auth-editorial">
        <span className="section-index">AUTODB MEMBERSHIP</span>
        <h1>
          Care that
          <br />
          <em>knows your car.</em>
        </h1>
        <p>
          Manage your vehicle care with the same attention to detail that
          defines every AutoDB service.
        </p>
        <div className="auth-rule" />
        <span className="auth-footnote">PRECISION · CARE · CONFIDENCE</span>
      </div>
      <div className="auth-card">
        <span className="section-index">
          {mode === "login" ? "WELCOME BACK" : "BEGIN YOUR JOURNEY"}
        </span>
        <h2>{mode === "login" ? "Sign in." : "Create your account."}</h2>
        <p className="muted">
          {mode === "login"
            ? "Access your appointments and service history."
            : "Set up your customer profile to book services."}
        </p>
        <form onSubmit={submit} className="form-stack">
          {mode === "register" && (
            <Field
              label="Full name"
              value={form.name}
              onChange={(v) => setForm({ ...form, name: v })}
              placeholder="Your full name"
              required
            />
          )}
          {mode === "register" && (
            <Field
              label="Phone number"
              type="tel"
              value={form.phone}
              onChange={(v) => setForm({ ...form, phone: v })}
              placeholder="Your phone number"
              required
            />
          )}
          <Field
            label="Email address"
            type="email"
            value={form.email}
            onChange={(v) => setForm({ ...form, email: v })}
            placeholder="you@example.com"
            required
          />
          <Field
            label="Password"
            type="password"
            value={form.password}
            onChange={(v) => setForm({ ...form, password: v })}
            placeholder="Enter your password"
            required
            minLength={8}
          />
          {mode === "register" && (
            <Field
              label="Confirm password"
              type="password"
              value={form.confirmPassword}
              onChange={(v) => setForm({ ...form, confirmPassword: v })}
              placeholder="Repeat your password"
              required
              minLength={8}
            />
          )}
          <p className="form-note">
            New accounts are registered as customers. Admin access is assigned
            by an administrator.
          </p>
          {(error || localError) && (
            <p className="form-error" role="alert">
              {localError || error}
            </p>
          )}
          {notice && (
            <p className="form-success" role="status">
              {notice}
            </p>
          )}
          <button className="button button-dark form-submit" disabled={loading}>
            {loading
              ? "PLEASE WAIT…"
              : mode === "login"
              ? "SIGN IN"
              : "CREATE ACCOUNT"}{" "}
            <span>↗</span>
          </button>
        </form>
        <p className="auth-switch">
          {mode === "login" ? "New to AutoDB?" : "Already have an account?"}{" "}
          <button
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
            }}
          >
            {" "}
            {mode === "login" ? "Create an account" : "Sign in"}
          </button>
        </p>
      </div>
    </section>
  );
}

function CustomerDashboard({
  user,
  data,
  nextAppointment,
  nextAppointmentError,
  navigate,
}) {
  const stats = data && !data.__error ? data : {};

  const upcomingCount = stats.upcomingAppointments ?? stats.upcoming_count ?? 0;

  const vehicleCount =
    stats.registeredVehicles ?? stats.vehicleCount ?? stats.vehicle_count ?? 0;

  const completedCount = stats.completedServices ?? stats.completed_count ?? 0;

  return (
    <section className="dashboard-page">
      <PageHeading
        eyebrow="YOUR AUTODB"
        title={
          <>
            A considered approach
            <br />
            <em>to every journey.</em>
          </>
        }
        description={`Welcome back${
          user?.name ? `, ${user.name.split(" ")[0]}` : ""
        }. Here's your vehicle care at a glance.`}
        action={
          <button
            className="button button-dark"
            onClick={() => navigate("book")}
          >
            BOOK A SERVICE <span>↗</span>
          </button>
        }
      />

      {data?.__error && (
        <ApiNotice
          text={`Dashboard data could not be loaded: ${data.__error}`}
        />
      )}

      <div className="stat-grid">
        <Stat
          label="UPCOMING APPOINTMENTS"
          value={upcomingCount}
          note="Your next scheduled visits"
        />

        <Stat
          label="REGISTERED VEHICLES"
          value={vehicleCount}
          note="Vehicles linked to your account"
        />

        <Stat
          label="COMPLETED SERVICES"
          value={completedCount}
          note="Your service history"
        />
      </div>

      <div className="dashboard-columns">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <span className="section-index">NEXT STEP</span>
              <h3>Your next service</h3>
            </div>
            <span className="panel-symbol">↗</span>
          </div>

          {nextAppointmentError ? (
            <ApiNotice text={nextAppointmentError} />
          ) : nextAppointment ? (
            <div className="next-appointment-details">
              <p>
                <strong>
                  {[nextAppointment.Brand, nextAppointment.Model]
                    .filter(Boolean)
                    .join(" ") || "Your vehicle"}
                </strong>
              </p>

              {nextAppointment.RegistrationNo && (
                <p className="muted">
                  Registration: {nextAppointment.RegistrationNo}
                </p>
              )}

              <p className="muted">
                Date:{" "}
                {nextAppointment.AppointmentDate
                  ? new Date(nextAppointment.AppointmentDate).toLocaleString()
                  : "To be confirmed"}
              </p>

              <p className="muted">
                Service: {nextAppointment.Complaint || "General service"}
              </p>

              <p className="muted">
                Status: {nextAppointment.AppointmentStatus || "Booked"}
              </p>
            </div>
          ) : (
            <p className="muted">
              You have no upcoming appointments. Book a service when your
              vehicle needs attention.
            </p>
          )}

          <button
            className="text-action"
            onClick={() => navigate("my-services")}
          >
            VIEW MY SERVICES <span>→</span>
          </button>
        </article>

        <article className="panel panel-dark">
          <span className="section-index">
            A LITTLE ATTENTION GOES A LONG WAY
          </span>

          <h3>
            Keep your vehicle
            <br />
            <em>at its best.</em>
          </h3>

          <p>
            Book maintenance, diagnostics or detailing whenever your vehicle
            needs it.
          </p>

          <button
            className="button button-light"
            onClick={() => navigate("book")}
          >
            SCHEDULE A SERVICE <span>↗</span>
          </button>
        </article>
      </div>
    </section>
  );
}

function BookService({
  user,
  booking,
  setBooking,
  onSubmit,
  loading,
  error,
  notice,
  requireCustomer,
  vehicles,
  vehiclesError,
}) {
  if (!user)
    return (
      <section className="simple-state">
        <span className="section-index">CUSTOMER ACCESS</span>
        <h1>
          Sign in to book
          <br />
          <em>your service.</em>
        </h1>
        <button className="button button-dark" onClick={requireCustomer}>
          CONTINUE TO SIGN IN <span>↗</span>
        </button>
      </section>
    );
  if (user.role !== "customer")
    return (
      <section className="simple-state">
        <h1>Booking is a customer feature.</h1>
        <p>Use the admin overview to manage incoming appointments.</p>
      </section>
    );
  return (
    <section className="form-page">
      <PageHeading
        eyebrow="APPOINTMENT REQUEST"
        title={
          <>
            Give your vehicle
            <br />
            <em>the right attention.</em>
          </>
        }
        description="Tell us what your vehicle needs. Your request will be sent to AutoDB for scheduling."
      />
      <form className="booking-card form-stack" onSubmit={onSubmit}>
        {vehiclesError && (
          <p className="form-error" role="alert">
            {vehiclesError}
          </p>
        )}
        {!vehiclesError && vehicles.length === 0 && (
          <p className="form-note">
            No registered vehicles were found. Please add a vehicle before
            booking.
          </p>
        )}
        <div className="form-grid">
          <label className="field">
            <span>Registered vehicle</span>
            <select
              value={booking.vehicle_id}
              onChange={(e) =>
                setBooking({
                  ...booking,
                  vehicle_id: e.target.value,
                })
              }
              required
            >
              <option value="">Choose your vehicle</option>
              {vehicles.map((vehicle) => (
                <option
                  key={vehicle.VehicleID}
                  value={String(vehicle.VehicleID)}
                >
                  {vehicle.Brand} {vehicle.Model} — {vehicle.RegistrationNo}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Service type</span>
            <select
              value={booking.serviceType}
              onChange={(e) =>
                setBooking({
                  ...booking,
                  serviceType: e.target.value,
                })
              }
            >
              <option>Routine Maintenance</option>
              <option>Engine & Diagnostics</option>
              <option>Premium Detailing</option>
              <option>General Inspection</option>
              <option>Other</option>
            </select>
          </label>
          <Field
            label="Preferred date"
            type="date"
            value={booking.date}
            onChange={(v) => setBooking({ ...booking, date: v })}
            required
            min={new Date().toISOString().slice(0, 10)}
          />
          <label className="field">
            <span>Preferred time</span>
            <select
              value={booking.time}
              onChange={(e) => setBooking({ ...booking, time: e.target.value })}
              required
            >
              <option value="">Choose a time</option>
              <option>09:00</option>
              <option>10:00</option>
              <option>11:00</option>
              <option>12:00</option>
              <option>14:00</option>
              <option>15:00</option>
              <option>16:00</option>
            </select>
          </label>
        </div>
        <label className="field">
          <span>Tell us a little more (optional)</span>
          <textarea
            rows="4"
            value={booking.description}
            onChange={(e) =>
              setBooking({
                ...booking,
                description: e.target.value,
              })
            }
            placeholder="Describe any concerns or specific requests…"
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {notice && (
          <p className="form-success" role="status">
            {notice}
          </p>
        )}
        <div className="form-submit-row">
          <p className="form-note">
            Your appointment is not confirmed until the service team reviews the
            request.
          </p>
          <button className="button button-dark" disabled={loading}>
            {loading ? "SUBMITTING…" : "SUBMIT REQUEST"} <span>↗</span>
          </button>
        </div>
      </form>
    </section>
  );
}

function MyServices({ appointments, error, navigate }) {
  return (
    <section className="dashboard-page">
      <PageHeading
        eyebrow="YOUR VEHICLE CARE"
        title={
          <>
            Every service,
            <br />
            <em>thoughtfully tracked.</em>
          </>
        }
        description="Review upcoming appointments and your maintenance history."
        action={
          <button
            className="button button-dark"
            onClick={() => navigate("book")}
          >
            NEW BOOKING <span>↗</span>
          </button>
        }
      />

      {error && <ApiNotice text={error} />}

      <div className="table-panel">
        <div className="table-title">
          <div>
            <span className="section-index">SERVICE RECORDS</span>
            <h3>Appointments &amp; history</h3>
          </div>
          <span className="muted">{appointments.length} records</span>
        </div>

        {appointments.length ? (
          <div className="responsive-table">
            <table>
              <thead>
                <tr>
                  <th>VEHICLE</th>
                  <th>SERVICE</th>
                  <th>DATE</th>
                  <th>STATUS</th>
                </tr>
              </thead>

              <tbody>
                {appointments.map((item, index) => {
                  const vehicleName =
                    [item.Brand, item.Model].filter(Boolean).join(" ") ||
                    item.vehicle ||
                    item.vehicle_name ||
                    "—";

                  const vehicleDisplay = item.RegistrationNo
                    ? `${vehicleName} (${item.RegistrationNo})`
                    : vehicleName;

                  const serviceName =
                    item.Complaint ||
                    item.serviceType ||
                    item.service_type ||
                    item.service ||
                    "General service";

                  const appointmentDate =
                    item.AppointmentDate || item.date || item.appointment_date;

                  const status =
                    item.ServiceStatus ||
                    item.AppointmentStatus ||
                    item.status ||
                    "Booked";

                  return (
                    <tr
                      key={
                        item.AppointmentID || item.ServiceID || item.id || index
                      }
                    >
                      <td>{vehicleDisplay}</td>

                      <td>{serviceName}</td>

                      <td>
                        {appointmentDate
                          ? new Date(appointmentDate).toLocaleString(
                              undefined,
                              {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                                hour: "numeric",
                                minute: "2-digit",
                              }
                            )
                          : "—"}
                      </td>

                      <td>
                        <StatusBadge status={status} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="Your service history will live here."
            body="Once appointments are returned by the backend, you’ll see booking status and completed service records on this page."
            action={() => navigate("book")}
            actionText="BOOK YOUR FIRST SERVICE"
          />
        )}
      </div>
    </section>
  );
}

function MyVehicles({
  vehicles,
  loading,
  error,
  formError,
  notice,
  form,
  setForm,
  onSubmit,
}) {
  const update = (field, value) =>
    setForm((current) => ({ ...current, [field]: value }));

  return (
    <section className="dashboard-page">
      <PageHeading
        eyebrow="YOUR GARAGE"
        title={
          <>
            Every vehicle,
            <br />
            <em>in one place.</em>
          </>
        }
        description="Register your vehicle to book services and keep its service history connected to your account."
      />

      <div className="dashboard-columns">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <span className="section-index">REGISTER A VEHICLE</span>
              <h3>Add to your garage</h3>
            </div>
          </div>

          <form className="form-stack" onSubmit={onSubmit}>
            <Field
              label="Registration number"
              value={form.registrationNo}
              onChange={(value) => update("registrationNo", value)}
              placeholder="e.g. GJ05AB1234"
              required
            />

            <Field
              label="Brand"
              value={form.brand}
              onChange={(value) => update("brand", value)}
              placeholder="e.g. Hyundai"
              required
            />

            <Field
              label="Model"
              value={form.model}
              onChange={(value) => update("model", value)}
              placeholder="e.g. Creta"
              required
            />

            <Field
              label="Manufacture year"
              type="number"
              value={form.manufactureYear}
              onChange={(value) => update("manufactureYear", value)}
              min="1886"
              placeholder="e.g. 2022"
            />

            <label className="field">
              <span>Fuel type (optional)</span>
              <select
                value={form.fuelType}
                onChange={(event) => update("fuelType", event.target.value)}
              >
                <option value="">Select fuel type</option>
                <option value="Petrol">Petrol</option>
                <option value="Diesel">Diesel</option>
                <option value="CNG">CNG</option>
                <option value="Electric">Electric</option>
                <option value="Hybrid">Hybrid</option>
                <option value="Other">Other</option>
              </select>
            </label>

            {formError && (
              <p className="form-error" role="alert">
                {formError}
              </p>
            )}
            {notice && (
              <p className="form-success" role="status">
                {notice}
              </p>
            )}

            <button
              className="button button-dark"
              type="submit"
              disabled={loading}
            >
              {loading ? "SAVING…" : "REGISTER VEHICLE"} <span>↗</span>
            </button>
          </form>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <span className="section-index">YOUR VEHICLES</span>
              <h3>Registered garage</h3>
            </div>
            <span className="muted">{vehicles.length} vehicles</span>
          </div>

          {error ? (
            <ApiNotice text={error} />
          ) : vehicles.length === 0 ? (
            <p className="muted">
              No vehicles registered yet. Add your first vehicle using the form.
            </p>
          ) : (
            <div className="vehicle-list">
              {vehicles.map((vehicle) => (
                <article className="panel" key={vehicle.VehicleID}>
                  <span className="section-index">
                    {vehicle.RegistrationNo}
                  </span>
                  <h3>
                    {vehicle.Brand} {vehicle.Model}
                  </h3>
                  <p className="muted">
                    Year: {vehicle.ManufactureYear || "Not specified"}
                  </p>
                  <p className="muted">
                    Fuel: {vehicle.FuelType || "Not specified"}
                  </p>
                </article>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}

function AdminDashboard({
  user,
  data,
  mechanics = [],
  mechanicsError = "",
  onAssignMechanic,
  onCreateStaff,
  staffSaving,
  staffNotice,
  staffError,
  appointments = [],
  appointmentsError = "",
  updatingAppointmentId,
  appointmentUpdateError,
  appointmentUpdateNotice,
  onUpdateAppointment,
  navigate,
}) {
  if (!user) {
    return (
      <section className="simple-state">
        <span className="section-index">RESTRICTED AREA</span>
        <h1>
          Admin access
          <br />
          <em>required.</em>
        </h1>
        <p>Sign in with an administrator account to manage AutoDB.</p>
        <button className="button button-dark" onClick={() => navigate("auth")}>
          SIGN IN <span>↗</span>
        </button>
      </section>
    );
  }

  if (user.role !== "admin") {
    return (
      <section className="simple-state">
        <h1>Administrator access required.</h1>
        <p>Your account does not have permission to view this area.</p>
        <button
          className="button button-dark"
          onClick={() => navigate("dashboard")}
        >
          BACK TO MY DASHBOARD
        </button>
      </section>
    );
  }

  const stats = data && !data.__error ? data : {};

  
const [staffForm, setStaffForm] = useState({
  name: "",
  email: "",
  phone: "",
  password: "",
});
const [staffFormError, setStaffFormError] = useState("");

const submitStaff = async (event) => {
  event.preventDefault();
  setStaffFormError("");

  if (staffForm.password.length < 12 || staffForm.password.length > 128) {
    setStaffFormError("Password must be between 12 and 128 characters.");
    return;
  }

  const success = await onCreateStaff(staffForm);

  if (success) {
    setStaffForm({
      name: "",
      email: "",
      phone: "",
      password: "",
    });
  }
};



  return (
    <section className="dashboard-page">
      <PageHeading
        eyebrow="AUTODB OPERATIONS"
        title={
          <>
            Service, in
            <br />
            <em>good hands.</em>
          </>
        }
        description="An overview for managing incoming requests and service operations."
        action={<span className="admin-role">ADMINISTRATOR</span>}
      />

      {data?.__error && (
        <ApiNotice text={`Admin data could not be loaded: ${data.__error}`} />
      )}

      
<section className="panel staff-management-panel">
  <div className="panel-heading">
    <div>
      <span className="section-index">TEAM MANAGEMENT</span>
      <h3>Add a mechanic</h3>
    </div>
    <span className="panel-symbol">+</span>
  </div>

  <p className="muted">
    Create a workshop employee account. New staff members are always
    assigned the Mechanic role.
  </p>

  <form className="form-stack" onSubmit={submitStaff}>
    <Field
      label="Full name"
      value={staffForm.name}
      onChange={(value) =>
        setStaffForm((current) => ({ ...current, name: value }))
      }
      placeholder="Mechanic's full name"
      required
    />

    <Field
      label="Email address"
      type="email"
      value={staffForm.email}
      onChange={(value) =>
        setStaffForm((current) => ({ ...current, email: value }))
      }
      placeholder="mechanic@example.com"
      required
    />

    <Field
      label="Phone number"
      type="tel"
      value={staffForm.phone}
      onChange={(value) =>
        setStaffForm((current) => ({ ...current, phone: value }))
      }
      placeholder="Phone number"
      required
    />

    <Field
      label="Initial password"
      type="password"
      value={staffForm.password}
      onChange={(value) =>
        setStaffForm((current) => ({ ...current, password: value }))
      }
      placeholder="At least 12 characters"
      minLength={12}
      required
    />

    {staffFormError && (
      <p className="form-error" role="alert">{staffFormError}</p>
    )}

    {staffError && (
      <p className="form-error" role="alert">{staffError}</p>
    )}

    {staffNotice && (
      <p className="form-success" role="status">{staffNotice}</p>
    )}

    <button
      className="button button-dark"
      type="submit"
      disabled={staffSaving}
    >
      {staffSaving ? "CREATING ACCOUNT..." : "CREATE MECHANIC ACCOUNT"}
      {" "}<span>↗</span>
    </button>
  </form>
</section>

      <div className="stat-grid">
        <Stat
          label="TOTAL APPOINTMENTS"
          value={stats.totalAppointments ?? "—"}
          note="All booking requests"
        />

        <Stat
          label="PENDING REQUESTS"
          value={stats.pendingRequests ?? "—"}
          note="Awaiting review"
        />

        <Stat
          label="CUSTOMERS"
          value={stats.totalCustomers ?? "—"}
          note="Registered customer accounts"
        />
      </div>

      <div className="table-panel">
        {appointmentUpdateError && <ApiNotice text={appointmentUpdateError} />}

        {appointmentUpdateNotice && (
          <p className="form-success" role="status">
            {appointmentUpdateNotice}
          </p>
        )}

        
<div className="table-panel">
  {appointmentUpdateError && <ApiNotice text={appointmentUpdateError} />}

  {appointmentUpdateNotice && (
    <p className="form-success" role="status">
      {appointmentUpdateNotice}
    </p>
  )}

  {!mechanicsError && mechanics.length === 0 && (
    <p className="muted">
      No active mechanics found. Create a mechanic account before assigning work.
    </p>
  )}

  <div className="table-title">
    <div>
      <span className="section-index">OPERATIONS</span>
      <h3>Appointment management</h3>
    </div>
    <span className="muted">
      {appointments.length}{" "}
      {appointments.length === 1 ? "appointment" : "appointments"}
    </span>
  </div>

  {/* Keep the rest of your existing appointment table here */}
</div>

        <div className="table-title">
          <div>
            <span className="section-index">OPERATIONS</span>
            <h3>Appointment management</h3>
          </div>

          <span className="muted">
            {appointments.length}{" "}
            {appointments.length === 1 ? "appointment" : "appointments"}
          </span>
        </div>

        {appointmentsError ? (
          <ApiNotice text={appointmentsError} />
        ) : appointments.length > 0 ? (
          <div className="responsive-table">
            <table>
              <thead>
                <tr>
                  <th>CUSTOMER</th>
                  <th>VEHICLE</th>
                  <th>SERVICE</th>
                  <th>DATE</th>
                  <th>STATUS</th>
                  <th>ASSIGNED MECHANIC</th>
                  <th>ACTION</th>
                </tr>
              </thead>

              <tbody>
                {appointments.map((item, index) => {
                  const vehicleName = [item.Brand, item.Model]
                    .filter(Boolean)
                    .join(" ");

                  const vehicleDisplay = [
                    vehicleName,
                    item.RegistrationNo ? `(${item.RegistrationNo})` : "",
                  ]
                    .filter(Boolean)
                    .join(" ");

                  const appointmentDate = item.AppointmentDate
                    ? new Date(item.AppointmentDate).toLocaleString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })
                    : "—";

                  return (
                    <tr key={item.AppointmentID ?? item.id ?? index}>
                      <td>{item.CustomerName || "—"}</td>

                      <td>{vehicleDisplay || "—"}</td>

                      <td>{item.Complaint || "General service"}</td>

                      <td>{appointmentDate}</td>

                      <td>
  <StatusBadge
    status={
      item.AppointmentStatus ||
      item.Status ||
      item.status ||
      "Booked"
    }
  />
</td>

<td>
  {mechanicsError ? (
    <span className="form-error">{mechanicsError}</span>
  ) : (
    <div className="appointment-actions">
      <select
        aria-label={`Mechanic for appointment ${item.AppointmentID}`}
        id={`appointment-mechanic-${item.AppointmentID}`}
        defaultValue={item.MechanicID ? String(item.MechanicID) : ""}
        disabled={
          updatingAppointmentId === item.AppointmentID ||
          ["In Progress", "Completed", "Cancelled"].includes(
            item.ServiceStatus || item.AppointmentStatus
          )
        }
      >
        <option value="">Choose mechanic</option>

        {mechanics.map((mechanic) => (
          <option
            key={mechanic.EmployeeID}
            value={String(mechanic.EmployeeID)}
          >
            {mechanic.Name}
          </option>
        ))}
      </select>

      <button
        type="button"
        className="button button-dark"
        disabled={
          updatingAppointmentId === item.AppointmentID ||
          mechanics.length === 0 ||
          ["In Progress", "Completed", "Cancelled"].includes(
            item.ServiceStatus || item.AppointmentStatus
          )
        }
        onClick={() => {
          const select = document.getElementById(
            `appointment-mechanic-${item.AppointmentID}`
          );

          if (!select?.value) {
            setAppointmentUpdateError(
              `Choose a mechanic for appointment #${item.AppointmentID}.`
            );
            return;
          }

          onAssignMechanic(item.AppointmentID, select.value);
        }}
      >
        {updatingAppointmentId === item.AppointmentID
          ? "ASSIGNING..."
          : item.MechanicID
          ? "REASSIGN"
          : "ASSIGN MECHANIC"}
      </button>
    </div>
  )}
</td>

                      <td>
                        <div className="appointment-actions">
                          <select
                            aria-label={`Status for appointment ${item.AppointmentID}`}
                            defaultValue={
                              item.AppointmentStatus ||
                              item.Status ||
                              item.status ||
                              "Booked"
                            }
                            id={`appointment-status-${item.AppointmentID}`}
                            disabled={
                              updatingAppointmentId === item.AppointmentID
                            }
                          >
                            <option value="Booked">Booked</option>
                            <option value="Pending">Pending</option>
                            <option value="Confirmed">Confirmed</option>
                            <option value="In Progress">In Progress</option>
                            <option value="Completed">Completed</option>
                            <option value="Cancelled">Cancelled</option>
                          </select>

                          <button
                            type="button"
                            className="button button-dark"
                            disabled={
                              updatingAppointmentId === item.AppointmentID
                            }
                            onClick={() => {
                              const select = document.getElementById(
                                `appointment-status-${item.AppointmentID}`
                              );

                              if (select) {
                                onUpdateAppointment(
                                  item.AppointmentID,
                                  select.value
                                );
                              }
                            }}
                          >
                            {updatingAppointmentId === item.AppointmentID
                              ? "SAVING..."
                              : "SAVE"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title={
              appointmentsError
                ? "Appointments could not be loaded."
                : "No appointment requests to display."
            }
            body={
              appointmentsError
                ? "Check the admin appointments API and try reloading the page."
                : "When appointments are returned by the backend, they will appear here."
            }
            action={() => navigate("home")}
            actionText="VIEW PUBLIC HOMEPAGE"
          />
        )}
      </div>
    </section>
  );
}

function Footer({ navigate, scrollTo }) {
  return (
    <footer className="footer">
      <button className="brand footer-brand" onClick={() => navigate("home")}>
        AUTO<span>DB</span>
        <small>THE ART OF AUTOMOTIVE CARE</small>
      </button>
      <p>Thoughtfully engineered for better journeys.</p>
      <div className="footer-bottom">
        <span>© 2026 AUTODB</span>
        <span>DESIGNED & DEVELOPED WITH CARE</span>
        <button onClick={() => scrollTo("home")}>BACK TO TOP ↑</button>
      </div>
    </footer>
  );
}
function PageHeading({ eyebrow, title, description, action }) {
  return (
    <div className="page-heading">
      <div>
        <span className="section-index">{eyebrow}</span>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="page-heading-action">{action}</div>}
    </div>
  );
}
function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  required,
  minLength,
  min,
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        minLength={minLength}
        min={min}
      />
    </label>
  );
}
function Stat({ label, value, note }) {
  return (
    <article className="stat-card">
      <span className="section-index">{label}</span>
      <strong>{value}</strong>
      <p>{note}</p>
    </article>
  );
}
function StatusBadge({ status }) {
  const value = String(status || "pending");
  return (
    <span
      className={`status-badge status-${value
        .toLowerCase()
        .replace(/[^a-z]+/g, "-")}`}
    >
      {value.replaceAll("_", " ")}
    </span>
  );
}
function EmptyState({ title, body, action, actionText }) {
  return (
    <div className="empty-state">
      <span className="empty-mark">A.</span>
      <h4>{title}</h4>
      <p>{body}</p>
      {action && (
        <button className="text-action" onClick={action}>
          {actionText} <span>→</span>
        </button>
      )}
    </div>
  );
}
function ApiNotice({ text }) {
  return (
    <div className="api-notice" role="status">
      <strong>Backend connection</strong>
      <span>{text}</span>
      <small>
        Confirm the API base URL and endpoint response shapes in{" "}
        <code>src/services/api.js</code>.
      </small>
    </div>
  );
}

function MechanicDashboard({
  user,
  services,
  loading,
  error,
  notice,
  completingServiceId,
  onStart,
  onComplete,
  onRefresh,
}) {
  const assigned = services.length;
  const inProgress = services.filter(
    (service) => service.ServiceStatus === "In Progress"
  ).length;
  const completed = services.filter(
    (service) => service.ServiceStatus === "Completed"
  ).length;

  return (
    <section className="dashboard-page">
      <PageHeading
        eyebrow="WORKSHOP OPERATIONS"
        title={
          <>
            Your assigned work,
            <br />
            <em>at a glance.</em>
          </>
        }
        description={`Welcome${
          user?.name ? `, ${user.name}` : ""
        }. Review your assigned services and update completed work.`}
        action={
          <button className="button button-dark" onClick={onRefresh}>
            REFRESH <span>↻</span>
          </button>
        }
      />

      {error && <ApiNotice text={error} />}
      {notice && (
        <p className="form-success" role="status">
          {notice}
        </p>
      )}

      <div className="stat-grid">
        <Stat
          label="ASSIGNED SERVICES"
          value={assigned}
          note="Jobs assigned to you"
        />
        <Stat label="IN PROGRESS" value={inProgress} note="Active work" />
        <Stat label="COMPLETED" value={completed} note="Finished services" />
      </div>

      <div className="table-panel">
        <div className="table-title">
          <div>
            <span className="section-index">MY WORK</span>
            <h3>Assigned services</h3>
          </div>
          <span className="muted">{assigned} records</span>
        </div>

        {loading ? (
          <p className="muted">Loading assigned services…</p>
        ) : services.length === 0 ? (
          <p className="muted">No services are currently assigned to you.</p>
        ) : (
          <div className="responsive-table">
            <table>
              <thead>
                <tr>
                  <th>SERVICE</th>
                  <th>CUSTOMER</th>
                  <th>VEHICLE</th>
                  <th>DATE</th>
                  <th>STATUS</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {services.map((service) => (
                  <tr key={service.ServiceID}>
                    <td>
                      #{service.ServiceID}
                      <br />
                      {service.Complaint || "General service"}
                    </td>
                    <td>{service.CustomerName || "—"}</td>
                    <td>
                      {[service.Brand, service.Model].filter(Boolean).join(" ")}
                      <br />
                      {service.RegistrationNo || "—"}
                    </td>
                    <td>
                      {service.AppointmentDate
                        ? new Date(service.AppointmentDate).toLocaleString()
                        : "—"}
                    </td>
                    <td>
                      <StatusBadge status={service.ServiceStatus} />
                    </td>
                    <td>
                      {service.ServiceStatus === "Pending" ? (
                        <button
                          className="button button-dark"
                          disabled={completingServiceId === service.ServiceID}
                          onClick={() => onStart(service.ServiceID)}
                        >
                          {completingServiceId === service.ServiceID
                            ? "STARTING…"
                            : "START SERVICE"}
                        </button>
                      ) : service.ServiceStatus === "In Progress" ? (
                        <button
                          className="button button-dark"
                          disabled={completingServiceId === service.ServiceID}
                          onClick={() => {
                            if (
                              window.confirm(
                                `Complete Service #${service.ServiceID}? This will deduct used parts from stock and update the invoice.`
                              )
                            ) {
                              onComplete(service.ServiceID);
                            }
                          }}
                        >
                          {completingServiceId === service.ServiceID
                            ? "COMPLETING…"
                            : "COMPLETE"}
                        </button>
                      ) : (
                        <span className="muted">No action</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

export default App;
