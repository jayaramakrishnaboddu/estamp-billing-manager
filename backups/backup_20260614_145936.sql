--
-- PostgreSQL database dump
--

\restrict Flkao6JNwP3Cb6mRbGAI0nE8KweVCGglDVvgwPJl85PcBFT1qTiy1WIbKGllks8

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: customers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customers (
    id integer NOT NULL,
    name character varying NOT NULL,
    phone character varying,
    current_balance integer
);


ALTER TABLE public.customers OWNER TO postgres;

--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.customers_id_seq OWNER TO postgres;

--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    customer_id integer,
    amount integer NOT NULL,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.payments OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payments_id_seq OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    id integer NOT NULL,
    certificate_number character varying NOT NULL,
    stamp_duty integer NOT NULL,
    service_charge integer NOT NULL,
    total_collected integer NOT NULL,
    payment_mode character varying NOT NULL,
    "timestamp" timestamp without time zone,
    customer_id integer,
    processed_by character varying(100)
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transactions_id_seq OWNER TO postgres;

--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying NOT NULL,
    password_hash character varying NOT NULL,
    role character varying
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: customers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.customers (id, name, phone, current_balance) FROM stdin;
2	rajesh	\N	0
5	krishna	\N	0
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (id, customer_id, amount, "timestamp") FROM stdin;
1	2	10	2026-06-12 15:37:40.358359
2	2	10	2026-06-12 15:37:47.396752
3	2	10	2026-06-12 15:37:48.877612
4	2	10	2026-06-12 15:43:04.35015
5	2	10	2026-06-12 15:46:17.401139
6	2	10	2026-06-12 15:54:10.779084
7	2	10	2026-06-12 15:57:27.47229
8	2	10	2026-06-12 15:57:37.672731
9	2	50	2026-06-13 04:09:31.27573
10	2	80	2026-06-14 04:25:59.21388
11	2	130	2026-06-14 04:26:31.856348
12	2	130	2026-06-14 04:27:48.331586
13	2	130	2026-06-14 06:22:07.255651
\.


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transactions (id, certificate_number, stamp_duty, service_charge, total_collected, payment_mode, "timestamp", customer_id, processed_by) FROM stdin;
17	IN-AP98326283769234X	100	30	130	cash	2026-06-14 07:35:16.442527	\N	admin
19	IN-DL23113129161075X	100	30	130	PhonePe	2026-06-14 07:52:04.209849	\N	admin
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, password_hash, role) FROM stdin;
1	admin	$2b$12$EvY1L6gqYvHKUqiOXqwfAusdPKCjMLqkPqvNTV/Hjo3PA6ZFINky.	admin
7	krishna	$2b$12$6VPs3M0fmqDDRmTxEX/YneoAypQxE61yCcaJg8nBN6cOjR3uSv3G6	admin
9	staff1	$2b$12$1o7J5nsGw/FWl0hv4gPfnu22HIt60RWqJUPRYqabHbndQN7I9C1MS	staff
\.


--
-- Name: customers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.customers_id_seq', 5, true);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payments_id_seq', 13, true);


--
-- Name: transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transactions_id_seq', 19, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 9, true);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_customers_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_customers_id ON public.customers USING btree (id);


--
-- Name: ix_customers_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_customers_name ON public.customers USING btree (name);


--
-- Name: ix_payments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_payments_id ON public.payments USING btree (id);


--
-- Name: ix_transactions_certificate_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_transactions_certificate_number ON public.transactions USING btree (certificate_number);


--
-- Name: ix_transactions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_id ON public.transactions USING btree (id);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: payments payments_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id);


--
-- Name: transactions transactions_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Flkao6JNwP3Cb6mRbGAI0nE8KweVCGglDVvgwPJl85PcBFT1qTiy1WIbKGllks8

