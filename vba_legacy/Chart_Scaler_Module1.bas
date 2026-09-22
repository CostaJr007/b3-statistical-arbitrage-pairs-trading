Sub EscalaAtivos()

    Dim nome As String
    
    Application.ScreenUpdating = False
    
    ActiveSheet.ChartObjects("Chart 2").Activate
    
    ActiveChart.Axes(xlValue, 1).Select
    
    With ActiveChart.Axes(xlValue, 1)
        .Crosses = xlMinimum - 0.1
        .MinimumScale = Range("D57").Value
        .MaximumScale = Range("E57").Value
        .MajorUnit = Range("F57")
        .TickLabels.NumberFormat = "0.00"
        .ReversePlotOrder = False
        .ScaleType = xlLinear
        .DisplayUnit = xlNone
    End With
    
    With ActiveChart.Axes(xlCategory, 1)
        .CategoryType = xlTimeScale
        .MajorUnit = Range("F56").Value
        .MinimumScale = Range("D56").Value
        .MaximumScale = Range("E56").Value
        .TickLabels.Orientation = 45
        .ReversePlotOrder = False

    End With
    
    
    With ActiveChart
         .HasAxis(xlCategory, xlPrimary) = True
         .HasAxis(xlCategory, xlSecondary) = False
    End With
    
    Application.ScreenUpdating = True

End Sub