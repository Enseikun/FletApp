import sys
from datetime import datetime

from src.models.azure.model_manager import ModelManager


def make_bar(ratio: float, length: int = 25) -> str:
    fill = int(length * ratio)
    bar = "#" * fill + "-" * (length - fill)
    return f"[{bar}] {int(ratio * 100):3d}%"


async def print_model_statuses_async(model_manager: ModelManager):
    try:
        lines = []
        for model_id, metrics in model_manager.get_all_metrics().items():
            try:
                status = "active"
                if metrics.disabled_until and datetime.now() < metrics.disabled_until:
                    status = "disabled"

                # 非同期でTPM取得
                current_tpm = await metrics.tpm_limiter.get_current_tpm()
                tpm_ratio = (
                    min(current_tpm / metrics.tpm_limiter.max_tpm, 1.0)
                    if metrics.tpm_limiter.max_tpm
                    else 0
                )
                rpm_ratio = (
                    min(metrics.rpm_counter / metrics.rpm_limit, 1.0)
                    if metrics.rpm_limit
                    else 0
                )
                lines.append(
                    f"status: {status}\n"
                    f"model_id: {model_id}\n"
                    f"tpm: {make_bar(tpm_ratio)} ({current_tpm}/{metrics.tpm_limiter.max_tpm})\n"
                    f"rpm: {make_bar(rpm_ratio)} ({metrics.rpm_counter}/{metrics.rpm_limit})\n"
                    f"latency: {metrics.get_average_latency():.2f}s\n"
                    f"disabled_until: {metrics.disabled_until if metrics.disabled_until else 'active'}\n"
                )
            except Exception as e:
                lines.append(f"model_id: {model_id}\nError: {str(e)}\n")

        output = "\n".join(lines)
        sys.stdout.write("\033[2J\033[H")  # ターミナルクリア
        sys.stdout.write(output)
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"\033[2J\033[HError visualizing model status: {str(e)}")
        sys.stdout.flush()
