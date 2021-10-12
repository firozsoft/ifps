from logic.models.abstract import BaseModel

class FIR(BaseModel):
    name = models.CharField("Name", max_length=4)

    class Meta:
        verbose_name = "FIR"
        verbose_name_plural = "FIRs"

