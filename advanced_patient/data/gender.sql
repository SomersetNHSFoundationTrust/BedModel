SELECT (Sum(Case When sexofpatientscode1 = 1 then 1 else 0 End)+0.0) / Count(*) n_male,
       (Sum(Case When sexofpatientscode1 = 2 then 1 else 0 End)+0.0) / Count(*) f_male,
       Case When em_el_dc = 'Elect' Then 'Elective'

            when em_el_dc = 'Emerg' and ActivityTreatmentfunctioncode in (120,140,107,103,104,110,106,144,991,100,101,655,108,130,502,503) Then 'Surgical Emergency' Else 'Medical Emergency' End type


FROM [CDS_APC].[dbo].[tblAPCCurrent]

Where SourceSys = 'TauntonandSomerset'
  and (WellBabyFlag = 0 or WellBabyFlagDerivied= 0)
  and EpisodeNumber = 1
  and SpellStartDate between dateadd(day, -29, getdate()) and dateadd(day, -1, getdate())
  and ActivityTreatmentfunctioncode in (120, 140, 450, 107, 330, 103, 301, 104, 110, 360, 106, 144, 991, 100, 101, 108, 306, 130, 502, 503, 180, 320, 401, 330, 307, 302, 301, 300, 430, 400, 314, 340, 410) -- Medical & Surgical
  and em_el_dc <> 'Dcase'
  and SexofPatientsCode1 in (1,2)

group by Case When em_el_dc = 'Elect' Then 'Elective'

              when em_el_dc = 'Emerg' and ActivityTreatmentfunctioncode in (120,140,107,103,104,110,106,144,991,100,101,655,108,130,502,503) Then 'Surgical Emergency' Else 'Medical Emergency' End