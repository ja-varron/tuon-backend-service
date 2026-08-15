-- Table: public.users
create table public.users (
  user_id uuid not null default gen_random_uuid (),
  email character varying not null,
  encrypted_password character varying not null,
  email_created_at timestamp with time zone null,
  constraint users_pkey primary key (user_id),
  constraint user_email_key unique (email)
) TABLESPACE pg_default;


-- Table: public.otp_flows
create table public.otp_flows (
  otp_flow_id uuid not null default gen_random_uuid (),
  user_id uuid not null default gen_random_uuid (),
  email character varying not null,
  otp_hash character varying not null,
  attempts smallint not null default '0'::smallint,
  expires_at timestamp with time zone not null,
  constraint otp_flows_pkey primary key (otp_flow_id),
  constraint otp_flows_email_key unique (email),
  constraint otp_flows_user_id_fkey foreign KEY (user_id) references users (user_id) on update CASCADE on delete CASCADE
) TABLESPACE pg_default;


-- Table: public.profiles
create table public.profiles (
  user_id uuid not null,
  email character varying not null,
  first_name character varying not null,
  middle_name character varying null,
  last_name character varying not null,
  role character varying not null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  institution_id uuid not null,
  examinee_id_number text not null default 'N/A'::text,
  constraint profiles_pkey primary key (user_id),
  constraint profiles_email_key unique (email),
  constraint profiles_user_id_fkey foreign KEY (user_id) references users (user_id) on delete CASCADE,
  constraint profiles_institution_id_fkey foreign KEY (institution_id) references institutions (institution_id) on update RESTRICT on delete RESTRICT,
  constraint profiles_email_check check ((length((email)::text) <= 50)),
  constraint profiles_last_name_check check ((length((last_name)::text) <= 30)),
  constraint profiles_middle_name_check check ((length((middle_name)::text) <= 20)),
  constraint profiles_examinee_id_number_check check ((length(examinee_id_number) <= 15)),
  constraint profiles_first_name_check check ((length((first_name)::text) <= 50))
) TABLESPACE pg_default;


-- Table: public.institutions
create table public.institutions (
  institution_id uuid not null default gen_random_uuid (),
  institution_name text not null,
  created_at timestamp with time zone not null default now(),
  constraint institutions_pkey primary key (institution_id)
) TABLESPACE pg_default;


-- Table: public.courses
create table public.courses (
  course_id uuid not null default gen_random_uuid (),
  institution_id uuid not null,
  course_name text not null,
  course_description text null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint course_pkey primary key (course_id),
  constraint course_institution_id_fkey foreign KEY (institution_id) references institutions (institution_id) on update CASCADE on delete CASCADE
) TABLESPACE pg_default;

create trigger set_courses_updated_at_trigger BEFORE
update on courses for EACH row
execute FUNCTION set_updated_at ();


-- Table: public.course_enrollment
create table public.course_enrollment (
  user_id uuid not null,
  course_id uuid not null,
  created_at timestamp with time zone not null default now(),
  constraint course_enrollment_pkey primary key (user_id, course_id),
  constraint course_enrollment_course_id_fkey foreign KEY (course_id) references courses (course_id) on update CASCADE on delete CASCADE,
  constraint course_enrollment_user_id_fkey foreign KEY (user_id) references profiles (user_id) on update CASCADE on delete CASCADE
) TABLESPACE pg_default;


-- Table: public.exams
create table public.exams (
  exam_id uuid not null default gen_random_uuid (),
  course_id uuid not null,
  exam_title text not null,
  exam_date timestamp with time zone null,
  passing_rate numeric null,
  created_by uuid not null,
  created_at timestamp with time zone not null default now(),
  topics character varying[] null,
  total_items numeric not null,
  constraint exam_pkey primary key (exam_id),
  constraint exam_course_id_fkey foreign KEY (course_id) references courses (course_id) on delete CASCADE,
  constraint exam_created_by_fkey foreign KEY (created_by) references profiles (user_id) on delete set null
) TABLESPACE pg_default;


-- Table: public.exam_papers
create table public.exam_papers (
  paper_id uuid not null default gen_random_uuid (),
  exam_id uuid not null,
  student_id uuid not null,
  actual_answers jsonb null,
  created_at timestamp with time zone not null default now(),
  constraint exam_papers_pkey primary key (paper_id),
  constraint exam_papers_exam_id_fkey foreign KEY (exam_id) references exams (exam_id) on update CASCADE on delete CASCADE,
  constraint exam_papers_student_id_fkey foreign KEY (student_id) references profiles (user_id) on update CASCADE on delete CASCADE
) TABLESPACE pg_default;


-- Table: public.answer_keys
create table public.answer_keys (
  key_id uuid not null default gen_random_uuid (),
  exam_id uuid not null,
  version smallint not null,
  answer_key jsonb not null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint answer_keys_pkey primary key (key_id),
  constraint answer_keys_exam_id_fkey foreign KEY (exam_id) references exams (exam_id) on update CASCADE on delete CASCADE
) TABLESPACE pg_default;


-- Table: public.score_results
create table public.score_results (
  exam_id uuid not null,
  student_id uuid not null,
  scores jsonb not null,
  scanned_at timestamp with time zone not null default now(),
  score_result_id uuid not null default gen_random_uuid (),
  constraint score_results_pkey primary key (score_result_id),
  constraint score_results_exam_id_fkey foreign KEY (exam_id) references exams (exam_id) on update CASCADE on delete CASCADE,
  constraint score_results_student_id_fkey foreign KEY (student_id) references profiles (user_id) on update CASCADE on delete CASCADE
) TABLESPACE pg_default;


-- Table: public.feedbacks
create table public.feedbacks (
  feedback_id uuid not null default gen_random_uuid (),
  exam_id uuid not null,
  student_id uuid not null,
  comment text not null,
  message_at timestamp with time zone not null default now(),
  constraint feedbacks_pkey primary key (feedback_id),
  constraint feedbacks_exam_id_fkey foreign KEY (exam_id) references exams (exam_id) on update CASCADE on delete CASCADE,
  constraint feedbacks_student_id_fkey foreign KEY (student_id) references profiles (user_id) on update CASCADE on delete CASCADE
) TABLESPACE pg_default;