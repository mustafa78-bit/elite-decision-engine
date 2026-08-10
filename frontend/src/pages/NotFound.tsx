import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "../components/ui/button";

export default function NotFound() {
  const navigate = useNavigate();
  const { t } = useTranslation("notFound");

  return (
    <div className="h-full flex flex-col items-center justify-center gap-4">
      <div className="text-4xl font-mono text-[var(--text-muted)]">404</div>
      <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-widest">
        {t("page.notFound")}
      </p>
      <Button variant="outline" onClick={() => navigate("/dashboard")}>
        {t("page.backToDashboard")}
      </Button>
    </div>
  );
}
