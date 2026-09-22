GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.courses TO tuon_api;

CREATE POLICY api_read_courses
ON public.courses
FOR SELECT
TO tuon_api
USING (is_admin());

CREATE POLICY admin_create_course
ON public.courses
FOR INSERT
TO tuon_api
WITH CHECK(is_admin())

CREATE POLICY admin_update_course
ON public.courses
FOR UPDATE
TO tuon_api
USING (is_admin())
WITH CHECK (is_admin());

CREATE POLICY admin_delete_course
ON public.courses
FOR DELETE
TO tuon_api
USING (is_admin())