# Matriz de trazabilidad — reglas, código y pruebas

El BRD fuente y la [matriz de necesidades–historias–reglas](../source/BRD_AulaPlus.pdf) son la base de las historias refinadas en [user-stories.md](../user-stories.md). Las pruebas automatizadas verifican los recorridos principales contra la API y el dominio.

| Historia / regla | Implementación principal | Pruebas |
|---|---|---|
| US-01 / BR-0001 — pago en 15 min y liberación | `BookingService.reserve`, `BookingService.pay`, `BookingService.release_expired`, agregado `Reserva` | `test_core_api_auto_assigns_tutor_persists_payment_and_documents_openapi`, `test_unpaid_reservation_expires_and_warns_near_deadline`, `test_reserva_confirms_within_15_minutes` |
| US-02 / BR-0002 — cierre de sesión | `SessionService.close_overdue`, agregado `Sesion` | `test_session_checklists_ratings_automatic_close_and_public_comment_reporting`, `test_session_auto_close_after_48h` |
| US-03 / BR-0003 — cancelación con motivo de soporte | `SessionService.cancel`, `Sesion.cancel` | `test_cancellation_requires_support_reason_and_applies_late_penalty`, `test_cancel_support_requires_reported_situation_br0003` |
| US-04 / BR-0004 — penalización del 50 % | `Pago.penalty_for`, `RefundCalculator` | `test_cancellation_requires_support_reason_and_applies_late_penalty`, `test_pago_late_cancellation_penalty_50_br0004` |
| US-05 / BR-0005 — desglose 20/80 | `Pago.confirm`, `BookingService.pay` | `test_core_api_auto_assigns_tutor_persists_payment_and_documents_openapi`, `test_pago_commission_20_80_br0005` |
| US-06 / BR-0006 — evitar traslapes | `OverlapValidator`, `BookingService.reserve` y `BookingService.pay` | `test_payment_failure_rolls_back_and_overlapping_confirmed_session_is_rejected`, `test_overlap_validator_br0006` |
| US-07 / BR-0007 — ventana de disputa | `DisputeService.report`, `WithinDisputeWindow` | `test_dispute_requires_support_role_evidence_and_resolves_with_refund`, `test_dispute_window_boundary` |
| US-08 / BR-0008 — ausencia del estudiante | `SessionService.report_student_absence`, `Sesion.mark_student_absent` | `test_attendance_no_shows_refunds_and_repeated_tutor_absences_suspend_account`, `test_connection_cut_threshold_and_student_absence_requires_tutor_presence` |
| US-09 / BR-0009 — reembolso y falta de tutor | `SessionService.report_tutor_absence`, `Tutor.register_absence` | `test_attendance_no_shows_refunds_and_repeated_tutor_absences_suspend_account` |
| US-10 / BR-0010 — corte de conexión | `SessionService.connection_cut`, `ConnectionCounts` | `test_connection_cut_threshold_and_student_absence_requires_tutor_presence`, `test_connection_cut_counts_as_completed_from_15_minutes`, `test_connection_cut_under_15_minutes_does_not_count` |
| US-11 / BR-0011 — SLA y escalamiento | `DisputeService.overdue`, `Disputa.due_at`, `Disputa.overdue` | `test_dispute_overdue_sla_br0011`, `test_dispute_requires_support_role_evidence_and_resolves_with_refund` |
| US-12 / BR-0012 — extensión consensuada | `SessionService.propose_extension`, `SessionService.accept_extension`, `Sesion` | `test_extension_and_modality_change_need_both_parties`, `test_extension_needs_both_parties_and_charges_proportionally` |
| US-13 / BR-0013 — cambio consensuado de modalidad | `SessionService.propose_modality`, `SessionService.accept_modality`, `Sesion` | `test_extension_and_modality_change_need_both_parties`, `test_modality_change_requires_both_and_one_hour_notice` |
| US-14 / BR-0014 — checklist y timestamps | `Sesion.confirm_checklist`, `Sesion.finish` | `test_session_checklists_ratings_automatic_close_and_public_comment_reporting`, `test_session_full_lifecycle_with_checklist_and_ratings_closes` |
| US-15 / BR-0015 — disponibilidad por materia | `Tutor.set_availability`, `SlotWithinAvailability` | `test_core_api_auto_assigns_tutor_persists_payment_and_documents_openapi`, `test_tutor_availability_and_rating`, `test_can_receive_booking_composite` |
| US-16 / BR-0016 — promedio y reportes | `TutorService.public_profile`, `SessionService.report_comment` | `test_session_checklists_ratings_automatic_close_and_public_comment_reporting`, `test_report_comment_marks_rating` |
| US-17 / BR-0017 — reembolso auditable | `Pago.refund`, `DisputeService.resolve` | `test_dispute_requires_support_role_evidence_and_resolves_with_refund`, `test_pago_refund_requires_reason_and_responsible` |
| US-18 / BR-0018 — suspensión tras ausencias | `Tutor.register_absence`, `TutorService.reactivate` | `test_attendance_no_shows_refunds_and_repeated_tutor_absences_suspend_account`, `test_tutor_suspended_after_more_than_two_absences_in_30_days` |
| US-19 / BR-0019 — dashboard semanal | `DashboardService.weekly`, `SqlDashboardReadModel.weekly` | `test_session_checklists_ratings_automatic_close_and_public_comment_reporting`, `test_api_validation_and_not_found_errors_are_explicit` |
| US-20 / BR-0020 — evidencia obligatoria para resolver | `Disputa.resolve`, `DisputeService.resolve` | `test_dispute_requires_support_role_evidence_and_resolves_with_refund`, `test_dispute_requires_evidence_decision_and_responsible_br0020` |

## Verificación de calidad

Ejecutar desde la raíz del proyecto:

```powershell
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=80
ruff check src tests scripts
```

La cobertura reportada debe provenir de la ejecución local o de CI de la revisión que se entregue; una cifra en documentación no reemplaza el reporte de cobertura.
