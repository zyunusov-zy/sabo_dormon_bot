import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import axiosInstance from "@/utils/axiosInstance";
import getRoleFromAccessToken from "../utils/getRoleJWT";

const StatusBadge = ({ status }) => {
  const map = {
    approved: { text: "Одобрено", className: "bg-green-100 text-green-800" },
    approved_by_doctor: {
      text: "Ожидание",
      className: "bg-yellow-100 text-yellow-800",
    },
    approved_by_accountant: {
      text: "Ожидание",
      className: "bg-yellow-100 text-yellow-800",
    },
    fully_approved: {
      text: "Одобрено",
      className: "bg-green-100 text-green-800",
    },
    rejected: { text: "Отклонено", className: "bg-red-100 text-red-800" },
    waiting: { text: "Ожидание", className: "bg-yellow-100 text-yellow-800" },
  };

  const s = map[status] || {
    text: status,
    className: "bg-gray-100 text-gray-800",
  };
  return <Badge className={s.className}>{s.text}</Badge>;
};

const ActionButtons = ({ patient, onApprove, onReject, userRole }) => {
  const isDoctor = userRole === "doctor";
  const isAccountant = userRole === "accountant";

  const alreadyActed =
    (isDoctor && (patient.approved_by_doctor || patient.rejected_by_doctor)) ||
    (isAccountant &&
      (patient.approved_by_accountant || patient.rejected_by_accountant));

  if (!isDoctor && !isAccountant) return null;
  if (alreadyActed) return null;

  return (
    <div className="flex gap-2">
      <Button
        size="sm"
        onClick={() => onApprove(patient.id, userRole)}
        className="bg-green-500 hover:bg-green-600 text-white"
      >
        Одобрить
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => onReject(patient.id, userRole)}
        className="border-red-500 text-red-500 hover:bg-red-50"
      >
        Отклонить
      </Button>
    </div>
  );
};

const ApprovalStatus = ({ patient }) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Врач:</span>
        {patient.approved_by_doctor ? (
          <Badge className="bg-green-100 text-green-800">Одобрено</Badge>
        ) : patient.rejected_by_doctor ? (
          <Badge className="bg-red-100 text-red-800">Отклонено</Badge>
        ) : (
          <Badge className="bg-yellow-100 text-yellow-800">Ожидание</Badge>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Бухгалтер:</span>
        {patient.approved_by_accountant ? (
          <Badge className="bg-green-100 text-green-800">Одобрено</Badge>
        ) : patient.rejected_by_accountant ? (
          <Badge className="bg-red-100 text-red-800">Отклонено</Badge>
        ) : (
          <Badge className="bg-yellow-100 text-yellow-800">Ожидание</Badge>
        )}
      </div>
    </div>
  );
};

const checkLateness = (dateStr, status) => {
  if (status === "fully_approved" || status === "rejected")
    return { late: false, days: 0 };

  const now = new Date();
  now.setDate(now.getDate() + 4);
  const date = new Date(dateStr);

  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  const late = diffDays > 3;

  return { late, days: diffDays };
};

// SVG Icons
const TotalIcon = () => (
  <svg
    className="w-8 h-8 text-blue-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
    />
  </svg>
);

const ApprovedIcon = () => (
  <svg
    className="w-8 h-8 text-green-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

const RejectedIcon = () => (
  <svg
    className="w-8 h-8 text-red-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

const PendingIcon = () => (
  <svg
    className="w-8 h-8 text-yellow-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

const LateIcon = () => (
  <svg
    className="w-8 h-8 text-orange-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
    />
  </svg>
);

export default function Dashboard() {
  const [statusFilter, setStatusFilter] = useState("Все");
  const [search, setSearch] = useState("");
  const [viewMode, setViewMode] = useState("table");
  const [patients, setPatients] = useState([]);
  const [userRole, setUserRole] = useState("");

  useEffect(() => {
    const role = getRoleFromAccessToken();
    if (role) {
      setUserRole(role);
    }
    const fetchPatients = async () => {
      try {
        const response = await axiosInstance.get("/api/patients/");
        setPatients(response.data);
      } catch (error) {
        console.error("Ошибка при загрузке пациентов:", error);
      }
    };

    fetchPatients();
  }, []);

  const handleApprove = async (patientId, role) => {
    try {
      const comment = "";

      await axiosInstance.post(`/api/patients/${patientId}/approve/`, {
        comment,
      });

      setPatients((prev) =>
        prev.map((p) => {
          if (p.id === patientId) {
            const updated = { ...p };
            if (role === "doctor") {
              updated.approved_by_doctor = true;
              updated.doctor_comment = comment;
            } else if (role === "accountant") {
              updated.approved_by_accountant = true;
              updated.accountant_comment = comment;
            }

            if (updated.approved_by_doctor && updated.approved_by_accountant) {
              updated.is_fully_approved = true;
              updated.status = "approved";
            }

            return updated;
          }
          return p;
        })
      );
    } catch (error) {
      console.error("Ошибка при одобрении:", error);
    }
  };

  const handleReject = async (patientId, role) => {
    try {
      const comment = "";

      await axiosInstance.post(`/api/patients/${patientId}/reject/`, {
        comment,
      });

      setPatients((prev) =>
        prev.map((p) => {
          if (p.id === patientId) {
            const updated = { ...p };
            if (role === "doctor") {
              updated.rejected_by_doctor = true;
              updated.doctor_comment = comment;
            } else if (role === "accountant") {
              updated.rejected_by_accountant = true;
              updated.accountant_comment = comment;
            }

            updated.is_rejected = true;
            updated.status = "rejected";

            return updated;
          }
          return p;
        })
      );
    } catch (error) {
      console.error("Ошибка при отклонении:", error);
    }
  };

  const filtered = patients.filter((p) => {
    const matchesStatus =
      statusFilter === "Все" ||
      (statusFilter === "Одобрено" && p.status === "fully_approved") ||
      (statusFilter === "Отклонено" && p.status === "rejected") ||
      (statusFilter === "Ожидание" &&
        (p.status === "waiting" ||
          p.status === "approved_by_doctor" ||
          p.status === "approved_by_accountant"));
    const matchesSearch = p.full_name
      .toLowerCase()
      .includes(search.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const total = patients.length;
  const approved = patients.filter((p) => p.status === "fully_approved").length;
  const rejected = patients.filter((p) => p.status === "rejected").length;
  const pending = patients.filter(
    (p) =>
      !p.approved_by_doctor ||
      !p.approved_by_accountant ||
      p.status === "waiting"
  ).length;

  const late = patients.filter(
    (p) => checkLateness(p.created_at, p.status).late
  ).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Панель управления пациентами
          </h1>
          <p className="text-gray-600">
            Управление и отслеживание заявок пациентов
          </p>
        </div>

        {/* Role Selector */}
        <div className="flex justify-center gap-4">
          <Badge className="bg-blue-100 text-blue-800 px-4 py-2">
              Текущая роль: {userRole === "doctor" ? "Врач" : "Бухгалтер"  }
          </Badge>
        </div>

        {/* Statistics Cards */}
        <div className="grid md:grid-cols-2 gap-4">
          {/* Main Statistics Card */}
          <Card className="bg-white shadow-md border hover:shadow-lg transition-shadow duration-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-800">
                  Статистика
                </h2>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                  <TotalIcon className="w-5 h-5 text-blue-600" />
                  <div>
                    <p className="text-xs text-gray-500">Всего</p>
                    <p className="text-xl font-bold text-blue-600">{total}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                  <ApprovedIcon className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="text-xs text-gray-500">Одобрено</p>
                    <p className="text-xl font-bold text-green-600">
                      {approved}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                  <RejectedIcon className="w-5 h-5 text-red-600" />
                  <div>
                    <p className="text-xs text-gray-500">Отклонено</p>
                    <p className="text-xl font-bold text-red-600">{rejected}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                  <PendingIcon className="w-5 h-5 text-yellow-600" />
                  <div>
                    <p className="text-xs text-gray-500">Ожидание</p>
                    <p className="text-xl font-bold text-yellow-600">
                      {pending}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Late Requests Card */}
          <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-md border hover:shadow-lg transition-shadow duration-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Просрочки</h2>
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              </div>

              <div className="flex items-center gap-4">
                <div className="bg-white/20 p-3 rounded-lg">
                  <LateIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm opacity-90">Просроченные заявки</p>
                  <p className="text-2xl font-bold">{late}</p>
                  <p className="text-xs opacity-75 mt-1">Требует внимания</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Controls */}
        <Card className="bg-white shadow-lg border-0">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center justify-between">
              <div className="flex gap-4 items-center">
                <Input
                  placeholder="Поиск пациентов..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="max-w-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="border-gray-300 hover:bg-gray-50"
                    >
                      Фильтр: {statusFilter}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    {["Все", "Одобрено", "Отклонено", "Ожидание"].map((s) => (
                      <DropdownMenuItem
                        key={s}
                        onClick={() => setStatusFilter(s)}
                      >
                        {s}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <div className="flex gap-2">
                <Button
                  variant={viewMode === "table" ? "default" : "outline"}
                  onClick={() => setViewMode("table")}
                  className={
                    viewMode === "table"
                      ? "bg-blue-500 hover:bg-blue-600"
                      : "border-gray-300 hover:bg-gray-50"
                  }
                >
                  Таблица
                </Button>
                <Button
                  variant={viewMode === "cards" ? "default" : "outline"}
                  onClick={() => setViewMode("cards")}
                  className={
                    viewMode === "cards"
                      ? "bg-blue-500 hover:bg-blue-600"
                      : "border-gray-300 hover:bg-gray-50"
                  }
                >
                  Карточки
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data View */}
        {viewMode === "table" ? (
          <Card className="bg-white shadow-lg border-0">
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      ID Пациента
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      ФИО
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Телефон
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Дата рождения
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Дата создания
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Одобрения
                    </th>
                    {/* <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Комментарии
                    </th> */}
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Google Drive
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Статус
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Просрочка
                    </th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filtered.map((p) => (
                    <tr
                      key={p.id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {p.patient_id}
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {p.full_name}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {p.phone_number}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {p.birth_date}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(p.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <ApprovalStatus patient={p} />
                      </td>
                      {/* <td className="px-4 py-3 text-gray-600 max-w-xs">
                        {p.doctor_comment && (
                          <div className="mb-1">
                            <span className="font-medium text-xs">Врач:</span>
                            <p className="text-xs">{p.doctor_comment}</p>
                          </div>
                        )}
                        {p.accountant_comment && (
                          <div>
                            <span className="font-medium text-xs">
                              Бухгалтер:
                            </span>
                            <p className="text-xs">{p.accountant_comment}</p>
                          </div>
                        )}
                      </td> */}
                      <td className="px-4 py-3 text-blue-600 underline">
                        <a
                          href={p.drive_folder_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Папка
                        </a>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={p.status} />
                      </td>
                      <td className="px-4 py-3">
                        {(() => {
                          const { late, days } = checkLateness(
                            p.created_at,
                            p.status
                          );
                          return late ? (
                            <span className="text-orange-500 font-semibold text-sm">
                              ⚠️ {days - 3} дн.
                            </span>
                          ) : (
                            <span className="text-green-600 text-sm">Нет</span>
                          );
                        })()}
                      </td>
                      <td className="px-4 py-3">
                        <ActionButtons
                          patient={p}
                          onApprove={handleApprove}
                          onReject={handleReject}
                          userRole={userRole}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((p) => (
              <Card
                key={p.id}
                className="bg-white shadow-lg border-0 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-gray-800">
                      {p.full_name}
                    </h3>
                    <span className="text-sm text-gray-500 font-mono">
                      {p.patient_id}
                    </span>
                  </div>

                  <div className="space-y-2 text-sm">
                    <p className="text-gray-600">
                      <span className="font-medium">Телефон:</span>{" "}
                      {p.phone_number}
                    </p>
                    <p className="text-gray-600">
                      <span className="font-medium">Дата рождения:</span>{" "}
                      {p.birth_date}
                    </p>
                    <p className="text-gray-600">
                      <span className="font-medium">Дата создания:</span>{" "}
                      {new Date(p.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <ApprovalStatus patient={p} />

                  {(p.doctor_comment || p.accountant_comment) && (
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <h4 className="font-medium text-sm mb-2">Комментарии:</h4>
                      {p.doctor_comment && (
                        <div className="mb-2">
                          <span className="font-medium text-xs">Врач:</span>
                          <p className="text-xs text-gray-600">
                            {p.doctor_comment}
                          </p>
                        </div>
                      )}
                      {p.accountant_comment && (
                        <div>
                          <span className="font-medium text-xs">
                            Бухгалтер:
                          </span>
                          <p className="text-xs text-gray-600">
                            {p.accountant_comment}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  <a
                    href={p.drive_folder_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline text-sm inline-block"
                  >
                    Папка Google Drive
                  </a>

                  <div className="flex items-center justify-between">
                    <StatusBadge status={p.status} />
                    {(() => {
                      const { late, days } = checkLateness(
                        p.created_at,
                        p.status
                      );
                      if (late) {
                        return (
                          <span className="text-orange-500 font-medium text-sm">
                            ⚠️ Просрочено — {days - 3} дн. назад
                          </span>
                        );
                      } else if (p.status === "pending") {
                        const remaining = 3 - days;
                        return (
                          <span className="text-yellow-600 font-medium text-sm">
                            ⏳ Осталось {remaining} дн.
                          </span>
                        );
                      }
                      return null;
                    })()}
                  </div>

                  <ActionButtons
                    patient={p}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    userRole={userRole}
                  />
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
